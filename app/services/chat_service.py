from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api import ChatRequest, ChatResponse, Citation
from app.services.orchestration_service import OrchestrationService


class ChatService:
    def __init__(self, orchestration_service: OrchestrationService) -> None:
        self._orchestration_service = orchestration_service

    async def chat(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        return await self._orchestration_service.run(session, request)

    async def stream_chat(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        async for event in self._orchestration_service.stream_run(session, request):
            yield event
