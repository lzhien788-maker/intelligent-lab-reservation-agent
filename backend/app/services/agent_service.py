from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.config import settings
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import agent_tools

SYSTEM_PROMPT = """你是智能实验室预约系统的 Agent，回答要简洁。

你可以使用这些工具：
1. search_lab_docs：查实验室的规章制度、安全须知、开放时间、预约流程等文档资料
2. list_open_labs：查当前开放中的实验室（拿到实验室ID、名称、位置、容量、开放时间）
3. list_lab_equipments：查某个实验室下的设备（需要 lab_id）
4. list_my_reservations：查当前用户自己的预约记录
5. create_lab_reservation：真正提交预约（写数据库）
6. get_today：获取服务器今天的日期

# 必须遵守
1. 用户提到「今天」「明天」「后天」「下周」这类相对日期时，必须先调用 get_today 拿到今天日期再换算，
   不要回答「我需要确定明天的具体日期」这种话。
2. 提交预约前，必须先向用户复述：实验室ID与名称、日期、开始时间、结束时间（若有设备则加设备ID与名称），
   并明确问「请确认是否进行预约？」。
3. 用户没有明确回复「确认」「确认预约」「就这样预约」之前，禁止调用 create_lab_reservation。
4. 缺 lab_id 就先调 list_open_labs 查出来；缺 equipment_id 就先调 list_lab_equipments 查出来，
   绝对不要自己编造数据库里没有的 ID。
5. 预约提交成功后状态是「待审核」，必须提示用户等管理员审核通过后才能使用。
6. 查实验室、查设备、查预约、查开放时间必须调用工具，不要凭记忆编造。
7. 工具返回 {"ok": false, "error": "..."} 时，把 error 里的原因如实告诉用户，不要假装预约成功。
"""
TOOL_LABELS = {
    "search_lab_docs": "检索实验室知识库",
    "list_open_labs": "查询开放的实验室",
    "list_lab_equipments": "查询实验室设备",
    "create_lab_reservation": "创建预约单",
    "get_today": "获取今天的日期"
}


def _build_history(data: ChatRequest) -> list:
    """前端的消息 转成LangChain的消息对象"""
    history = []
    for message in data.messages:
        content = (message.content or "").strip()
        if not content:
            continue
        if message.role == "user":
            history.append(HumanMessage(content=content))
        elif message.role == "assistant":
            history.append(AIMessage(content=content))
    if not history:
        raise BusinessException(message="请输入您的对话内容")
    return history

def _tool_output_preview(output: Any, limit: int = 220):
    if isinstance(output, ToolMessage):
        output = output.content
    text = (
        output if isinstance(output, str) else str(output)
    )
    return text if len(text) <= limit else text[:limit] + "..."

def _chunk_text(chunk: Any):
    """
    从模型的流式输出里面 拿到纯文本
    chunk.comtent 可能str[{type, text}, ...]等类型 这个需要统一处理成字符串
    """
    if chunk is None:
        return ""
    # chunk 如果是 AiMessage 类型的 则可以取出 content
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text") or "")
        return "".join(parts)
    return str(content) if content is not None else ""


async def stream_agent(db: Session, current_user: User, data: ChatRequest):
    """
    生成器：边跑 agent 边 yield 事件，给前端做 SSE 流式输出
    事件类型：status | tool_start | tool_end | token | done | error
    注意：必须是 async 生成器 + astream_events，同步的 stream_events 在 langgraph 1.x 不支持
    """
    try:
        history = _build_history(data)
        agent = build_agent(db, current_user)
        inputs = {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]}

        yield {"type": "status", "message": "正在思考…"}

        async for event in agent.astream_events(
            inputs, version="v2", config={"recursion_limit": 25}
        ):
            kind = event.get("event")

            if kind == "on_tool_start":
                name = event.get("name") or ""
                yield {
                    "type": "tool_start",
                    "name": name,
                    "label": TOOL_LABELS.get(name, name),
                }

            elif kind == "on_tool_end":
                name = event.get("name") or ""
                output = (event.get("data") or {}).get("output")
                yield {
                    "type": "tool_end",
                    "name": name,
                    "label": TOOL_LABELS.get(name, name),
                    "preview": _tool_output_preview(output),
                }

            elif kind == "on_chat_model_stream":
                # 只取 agent 节点吐出的文字，工具节点内部的模型调用不要混进来
                metadata = event.get("metadata") or {}
                if metadata.get("langgraph_node") not in (None, "agent"):
                    continue
                text = _chunk_text((event.get("data") or {}).get("chunk"))
                if not text:
                    continue  # 工具调用的参数分片 content 为空，跳过
                yield {"type": "token", "content": text}

        yield {"type": "done"}
    except BusinessException as e:
        yield {"type": "error", "message": e.message}
    except Exception as exc:
        print(f"[AgentStream] 执行失败：{type(exc).__name__}: {exc}")
        yield {"type": "error", "message": "大模型调用失败，请稍后重试"}

def build_agent(db: Session, current_user: User):
    """组装 LangGraph 工作流：agent 节点（大模型）+ tools 节点（执行工具）"""
    tools = agent_tools.build_tools(db, current_user)
    llm = ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0,
        streaming=True,
    ).bind_tools(tools)  # 关键：把工具绑定给大模型，它才知道自己能调工具

    def agent_node(state: MessagesState):
        """LangGraph 执行工作流的节点：把整段对话丢给大模型"""
        response = llm.invoke(state["messages"])
        # 注意 key 必须是 messages（复数），写 message 的话状态不会更新，工具永远不会被调用
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    # 条件边：模型这次要调工具就进 tools 节点，不要调就直接结束
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()



def run_agent(data: ChatRequest, db: Session, current_user: User) -> ChatMessage:
    """大模型对话入口：把前端传来的历史转成 LangChain 消息，跑一遍图，取最终回复"""
    if not data.messages:
        raise BusinessException(message="对话内容为空")

    history = []
    for message in data.messages:
        content = (message.content or "").strip()
        if not content:
            continue
        if message.role == "user":
            history.append(HumanMessage(content=content))
        elif message.role == "assistant":
            history.append(AIMessage(content=content))

    if not history:
        raise BusinessException(message="请输入您要对话的内容")
    if not isinstance(history[-1], HumanMessage):
        raise BusinessException(message="最后一条消息必须是用户提问")

    agent = build_agent(db, current_user)
    try:
        result = agent.invoke(
            {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]},
            # 一次预约可能要走：get_today → list_open_labs → create_lab_reservation，
            # 每调一次工具算两轮，10 轮不够用，给到 25 轮
            config={"recursion_limit": 25},
        )
    except BusinessException:
        raise
    except Exception as exc:
        print(f"[Agent] 执行失败：{type(exc).__name__}: {exc}")
        raise BusinessException(message="大模型调用失败，请稍后重试")

    messages = result.get("messages") or []
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            if str(content).strip():
                return ChatMessage(role="assistant", content=str(content).strip())

    raise BusinessException(message="大模型没有任何返回内容")
