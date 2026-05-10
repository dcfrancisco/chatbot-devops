from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.models.api import ChatRequest, ChatResponse
from app.orchestration.service import OrchestrationService


class ConversationAgent(BaseAgent[ChatRequest, ChatResponse]):
    name = "conversation"
    description = "Default retrieval-first conversational agent for the platform runtime."
    capabilities = ("chat", "rag", "memory", "tool-use")

    def __init__(self, orchestration_service: OrchestrationService) -> None:
        self._orchestration_service = orchestration_service

    async def run(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        return await self._orchestration_service.run(session, request)

    async def stream(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        async for event in self._orchestration_service.stream_run(session, request):
            yield event