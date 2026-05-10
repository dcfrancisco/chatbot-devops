from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_container, get_session
from app.core.container import ServiceContainer
from app.models.api import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    container: ServiceContainer = Depends(get_container),
    session: AsyncSession = Depends(get_session),
):
    if request.stream:
        stream = container.chat_service.stream_chat(session, request)
        return StreamingResponse(stream, media_type="text/event-stream")
    return await container.chat_service.chat(session, request)
