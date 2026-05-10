from app.shared.registration import FactoryCatalog, register_factory
from app.workflows.base import BaseWorkflow
from app.workflows.defaults import ChatWorkflow
from app.workflows.registry import WorkflowRegistry


WORKFLOW_CATALOG = FactoryCatalog[BaseWorkflow]()


@register_factory(WORKFLOW_CATALOG, name="chat-turn", capabilities=("chat", "retrieval", "tools", "memory"), metadata={"kind": "workflow"})
def build_chat_workflow() -> BaseWorkflow:
    return ChatWorkflow()


def build_workflow_registry() -> WorkflowRegistry:
    return WorkflowRegistry(WORKFLOW_CATALOG.build_all())