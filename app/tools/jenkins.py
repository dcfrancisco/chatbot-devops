from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.integrations.jenkins.service import JenkinsService
from app.tools.base import Tool, ToolExecutionContext


class JenkinsToolArguments(BaseModel):
    action: Literal["list_jobs", "get_job", "create_job"]
    name: str | None = Field(default=None, min_length=1)
    config_xml: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_action_payload(self) -> "JenkinsToolArguments":
        if self.action in {"get_job", "create_job"} and not self.name:
            raise ValueError("'name' is required for get_job and create_job actions")
        if self.action == "create_job" and not self.config_xml:
            raise ValueError("'config_xml' is required for create_job action")
        return self


class JenkinsTool(Tool[JenkinsToolArguments]):
    name = "jenkins"
    description = "Interact with the configured Jenkins instance for safe read and create operations."
    tags = ("jenkins", "ci", "integration")
    timeout_seconds = 20.0
    retry_attempts = 2
    arguments_model = JenkinsToolArguments

    def __init__(self, jenkins_service: JenkinsService) -> None:
        self._jenkins_service = jenkins_service

    def metadata(self) -> dict[str, object]:
        return {"supported_actions": ["list_jobs", "get_job", "create_job"]}

    async def execute(self, context: ToolExecutionContext, arguments: JenkinsToolArguments) -> dict[str, object]:
        del context
        if arguments.action == "list_jobs":
            return {"action": arguments.action, "result": await self._jenkins_service.list_jobs()}
        if arguments.action == "get_job":
            return {"action": arguments.action, "result": await self._jenkins_service.get_job(name=arguments.name or "")}
        return {
            "action": arguments.action,
            "result": await self._jenkins_service.create_job(
                name=arguments.name or "",
                config_xml=arguments.config_xml or "",
            ),
        }