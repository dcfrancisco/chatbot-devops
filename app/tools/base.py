from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api import ToolDescriptor


class EmptyToolArguments(BaseModel):
    pass


@dataclass(slots=True)
class ToolExecutionContext:
    session: AsyncSession
    trace_id: str


ArgumentsT = TypeVar("ArgumentsT", bound=BaseModel)


class BaseTool(ABC, Generic[ArgumentsT]):
    name: str
    description: str
    tags: tuple[str, ...] = ()
    timeout_seconds: float = 10.0
    retry_attempts: int = 1
    safe_execution: bool = True
    arguments_model: type[ArgumentsT] = EmptyToolArguments

    def describe(self) -> ToolDescriptor:
        return ToolDescriptor(
            name=self.name,
            description=self.description,
            tags=list(self.tags),
            timeout_seconds=self.timeout_seconds,
            retry_attempts=self.retry_attempts,
            safe_execution=self.safe_execution,
            input_schema=self.arguments_model.model_json_schema(),
            metadata=self.metadata(),
        )

    def metadata(self) -> dict[str, Any]:
        return {}

    def validate_arguments(self, arguments: dict[str, Any]) -> ArgumentsT:
        return self.arguments_model.model_validate(arguments)

    def trace_payload(self, arguments: ArgumentsT) -> dict[str, Any]:
        return {"argument_keys": sorted(arguments.model_dump(exclude_none=True).keys())}

    @abstractmethod
    async def execute(self, context: ToolExecutionContext, arguments: ArgumentsT) -> dict[str, Any]:
        raise NotImplementedError


Tool = BaseTool
