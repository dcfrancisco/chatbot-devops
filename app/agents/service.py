from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.models.api import ChatRequest, ChatResponse
from app.observability.service import ObservabilityService
from app.observability.tracing.models import SpanKind


class ChatService:
    def __init__(
        self,
        agent_registry: AgentRegistry,
        observability_service: ObservabilityService,
        default_agent_name: str = "conversation",
    ) -> None:
        self._agent_registry = agent_registry
        self._observability_service = observability_service
        self._default_agent_name = default_agent_name

    async def chat(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        agent_name = request.agent_name or self._default_agent_name
        async with self._observability_service.span(
            "agent.run",
            kind=SpanKind.AGENT_EXECUTION,
            component="agents",
            agent_name=agent_name,
        ):
            agent = self._agent_registry.get(agent_name)
            return await agent.run(session, request)

    async def stream_chat(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        agent_name = request.agent_name or self._default_agent_name
        async with self._observability_service.span(
            "agent.stream",
            kind=SpanKind.AGENT_EXECUTION,
            component="agents",
            agent_name=agent_name,
        ):
            agent = self._agent_registry.get(agent_name)
            async for event in agent.stream(session, request):
                yield event