from app.shared.registry import ComponentNotFoundError, NamedRegistry
from app.tools.base import Tool


class ToolNotFoundError(KeyError):
    pass


class ToolRegistry(NamedRegistry[Tool]):
    def get(self, name: str) -> Tool:
        try:
            return super().get(name)
        except ComponentNotFoundError as exc:
            raise ToolNotFoundError(f"Unknown tool: {name}") from exc
