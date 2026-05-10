from app.workflows.base import BaseWorkflow


class ChatWorkflow(BaseWorkflow):
    name = "chat-turn"
    description = "Default workflow for a single retrieval-first conversational turn."
    tags = ("chat", "retrieval", "tools", "memory")