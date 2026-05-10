from abc import ABC


class BaseWorkflow(ABC):
    name: str
    description: str
    tags: tuple[str, ...] = ()

    def metadata(self) -> dict[str, object]:
        return {"tags": list(self.tags)}