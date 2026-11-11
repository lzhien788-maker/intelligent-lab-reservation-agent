import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services import agent_service

router = APIRouter(prefix="/ai", tags=["AI相关的API"])


@router.post("/chat")
def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 一次性返回完整回答（非流式）
    message = agent_service.run_agent(data, db, current_user)
    return Response.success(data=message)


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 流式输出：把 stream_agent 产出的一条条事件实时推给前端"""

    async def event_gen():
        async for event in agent_service.stream_agent(db, current_user, data):
            # SSE 规范：每条消息必须是 "data: xxx\n\n"，末尾两个换行表示这一条结束
            # 必须 json.dumps，否则前端拿到 Python 字典的 str（单引号），JSON.parse 会失败
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 关闭 nginx 缓冲，保证边生成边推送
        },
    )
