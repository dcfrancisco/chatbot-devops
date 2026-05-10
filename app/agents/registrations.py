from typing import Any

from app.agents.base import BaseAgent
from app.agents.chat import ConversationAgent
from app.agents.registry import AgentRegistry
from app.orchestration.service import OrchestrationService
from app.shared.registration import FactoryCatalog, register_factory


AGENT_CATALOG = FactoryCatalog[BaseAgent[Any, Any]]()


@register_factory(AGENT_CATALOG, name="conversation", capabilities=("chat", "rag", "memory", "tool-use"), metadata={"kind": "agent"})
def build_conversation_agent(*, orchestration_service: OrchestrationService) -> BaseAgent[Any, Any]:
    return ConversationAgent(orchestration_service)


def build_agent_registry(*, orchestration_service: OrchestrationService) -> AgentRegistry:
    return AgentRegistry(AGENT_CATALOG.build_all(orchestration_service=orchestration_service))