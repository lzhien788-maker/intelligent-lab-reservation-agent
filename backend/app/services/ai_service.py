import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.config import settings
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import equipment_service, kb_service, lab_service, reservation_service

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答，不要编造资料里没有的时间、规则、设备。
你可以调用工具查询真实的实验室列表、实验室设备、预约记录；需要这些实时数据时必须调用工具，不要凭记忆回答。
如果工具返回的结果里没有用户问的信息，就如实说查不到。
除了实验室相关的问题之外,不用回复用户不相关的问题
"""

# 最多连续调用几轮工具（防止模型来回死循环）
MAX_TOOL_ROUNDS = 5

STATUS_TEXT = {0: "待审核", 1: "已通过", 2: "已拒绝", 3: "已取消"}

# 给大模型的「工具说明书」：告诉它能调用哪些工具、每个工具要什么参数
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_open_labs",
            "description": "查询当前开放中的实验室列表，可按名称关键字筛选。用户问有哪些实验室、某个实验室在哪、能坐多少人时调用",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "实验室名称关键字，比如「化学」「计算机」；可以为空，为空则查全部开放实验室",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_lab_equipments",
            "description": "查询某个实验室下的设备列表（型号、数量、是否可预约）。用户问某个实验室有什么设备时调用，lab_id 从 list_open_labs 的结果里取",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_id": {"type": "integer", "description": "实验室 ID"},
                    "keywords": {
                        "type": "string",
                        "description": "设备名称关键字；可以为空",
                    },
                },
                "required": ["lab_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_my_reservations",
            "description": "查询当前登录用户自己的预约记录（实验室预约和设备预约）。用户问「我的预约」「我约了什么时候」「通过没有」时调用",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "integer",
                        "description": "预约状态：0待审核 1已通过 2已拒绝 3已取消；不传则查全部",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_reservations",
            "description": "查询全站所有预约记录，仅管理员可用。管理员问「有哪些预约」「最近谁约了什么」时调用",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "integer",
                        "description": "预约状态：0待审核 1已通过 2已拒绝 3已取消；不传则查全部",
                    }
                },
            },
        },
    },
]


def run_tool(db: Session, name: str, arguments: str, current_user: User | None = None) -> str:
    """按工具名分发到对应的业务查询函数，返回 json 字符串给大模型"""
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "参数不是合法的json"}, ensure_ascii=False)

    print(f"[工具] 调用 {name} 参数={args}")

    try:
        if name == "list_open_labs":
            keywords = (args.get("keywords") or "").strip() or None
            page = lab_service.get_lab_page(db, page=1, page_size=10, keywords=keywords, status=1)
            rows = []
            for item in page.list:
                rows.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "location": item.location,
                        "capacity": item.capacity,
                        "open_time": item.open_time,
                        "close_time": item.close_time,
                    }
                )
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)

        if name == "list_lab_equipments":
            lab_id = args.get("lab_id")
            if not lab_id:
                return json.dumps({"error": "缺少实验室参数 lab_id，请先调用 list_open_labs 拿到 id"}, ensure_ascii=False)
            keywords = (args.get("keywords") or "").strip() or None
            page = equipment_service.get_equipment_page(
                db, page=1, page_size=10, lab_id=int(lab_id), keywords=keywords
            )
            rows = []
            for item in page.list:
                rows.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "lab_id": item.lab_id,
                        "spec": item.spec,
                        "quantity": item.quantity,
                        "status": "可预约" if item.status == 1 else "维修中",
                    }
                )
            return json.dumps({"total": page.total, "equipments": rows}, ensure_ascii=False)

        if name in ("list_my_reservations", "list_all_reservations"):
            if name == "list_all_reservations" and (current_user is None or current_user.role != "admin"):
                return json.dumps({"error": "只有管理员可以查看全部预约"}, ensure_ascii=False)
            status = args.get("status")
            if status is not None:
                status = int(status)
            page = reservation_service.get_reservation_page(
                db,
                current_user,
                page=1,
                page_size=10,
                status=status,
                only_mine=(name == "list_my_reservations"),
                auto_cancel=False,   # 只是查，不要顺手改数据
            )
            rows = []
            for item in page.list:
                rows.append(
                    {
                        "id": item.id,
                        "user_name": item.user_name,
                        "lab_name": item.lab_name,
                        "equipment_name": item.equipment_name or "未预约设备",
                        "type": item.type,
                        "reserve_date": item.reserve_date,
                        "time": f"{item.start_time}-{item.end_time}",
                        "status": STATUS_TEXT.get(item.status, str(item.status)),
                        "remark": item.remark,
                    }
                )
            return json.dumps({"total": page.total, "reservations": rows}, ensure_ascii=False)

        return json.dumps({"error": f"未找到工具: {name}"}, ensure_ascii=False)
    except Exception as exc:
        print(f"[工具] {name} 执行失败：{type(exc).__name__}: {exc}")
        return json.dumps({"error": f"工具执行失败: {exc}"}, ensure_ascii=False)


def get_client() -> OpenAI:
    """创建openai客户端"""
    if not settings.LLM_API_KEY:
        raise BusinessException(message="未获取到大模型API Key")
    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def chat(data: ChatRequest, db: Session | None = None, current_user: User | None = None) -> ChatMessage:
    """接收前端传来的多轮历史，返回一条 assistant 消息（内部可能多次调用工具）"""
    if not data.messages:
        raise BusinessException(message="对话内容为空")

    history = []
    for message in data.messages:
        if message.role in ("user", "assistant") and message.content.strip():
            history.append(message.model_dump())
    if not history:
        raise BusinessException(message="请输入您要的对话内容")

    question = next(
        (item["content"] for item in reversed(history) if item["role"] == "user"), ""
    )

    knowledge = kb_service.search(query=question)
    system_prompt = SYSTEM_PROMPT
    if knowledge:
        system_prompt += "\n\n以下是检索到的实验室资料:\n" + knowledge

    messages = [{"role": "system", "content": system_prompt}, *history]

    client = get_client()

    # 工具调用可能来回好几轮：模型要工具 -> 我们执行 -> 把结果喂回去 -> 模型再决定
    for _ in range(MAX_TOOL_ROUNDS):
        try:
            res = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            # 真实原因打到控制台，方便排查；给前端的仍是友好提示
            print(f"[AI] 调用大模型失败：{type(e).__name__}: {e}")
            raise BusinessException(message="大模型调用失败,请稍后重试")

        msg = res.choices[0].message
        tool_calls = msg.tool_calls or []

        # 没有工具调用：模型直接把答案说完了，这就是最终回复
        if not tool_calls:
            content = msg.content
            if not content or not content.strip():
                raise BusinessException(message="大模型没有返回内容")
            return ChatMessage(role="assistant", content=content.strip())

        # 有工具调用：先把「模型要求调用工具」这条消息放进历史（OpenAI 协议要求）
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in tool_calls
                ],
            }
        )

        # 逐个执行工具，把结果按 tool_call_id 对回去
        for call in tool_calls:
            result = run_tool(db, call.function.name, call.function.arguments, current_user)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )

    # 轮数用完了还没给答案，别把空回复丢给前端
    return ChatMessage(role="assistant", content="这个我查了好几次还没查出来，换个说法再问问？")
