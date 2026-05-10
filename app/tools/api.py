from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.integrations.api.service import ApiService
from app.tools.base import Tool, ToolExecutionContext


class ApiToolArguments(BaseModel):
    integration: str = Field(min_length=1)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    path: str = Field(min_length=1)
    query: dict[str, Any] = Field(default_factory=dict)
    json_body: dict[str, Any] | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.startswith("/") or "://" in value:
            raise ValueError("path must be a relative path starting with '/'")
        return value


class ApiTool(Tool[ApiToolArguments]):
    name = "api"
    description = "Call a configured API integration using a safe allowlisted client."
    tags = ("api", "integration")
    timeout_seconds = 15.0
    retry_attempts = 2
    arguments_model = ApiToolArguments

    def __init__(self, api_service: ApiService) -> None:
        self._api_service = api_service

    def metadata(self) -> dict[str, object]:
        return {"configured_integrations": self._api_service.list_integrations()}

    async def execute(self, context: ToolExecutionContext, arguments: ApiToolArguments) -> dict[str, object]:
        del context
        return await self._api_service.request(
            integration_name=arguments.integration,
            method=arguments.method,
            path=arguments.path,
            query=arguments.query,
            json_body=arguments.json_body,
            headers=arguments.headers,
        )