from app.shared.registry import NamedRegistry
from app.workflows.base import BaseWorkflow


class WorkflowRegistry(NamedRegistry[BaseWorkflow]):
    def default(self) -> BaseWorkflow:
        return self.get("chat-turn")