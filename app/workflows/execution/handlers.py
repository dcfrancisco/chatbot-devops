from __future__ import annotations

import inspect
from typing import Any, Protocol

from app.workflows.definitions import WorkflowStepDefinition
from app.workflows.execution.context import WorkflowExecutionContext
from app.workflows.execution.models import WorkflowStepOutcome
from app.workflows.state import WorkflowStepStatus


class WorkflowStepHandler(Protocol):
    name: str

    async def handle(self, context: WorkflowExecutionContext, step: WorkflowStepDefinition) -> WorkflowStepOutcome:
        ...


class StepHandlerNotFoundError(KeyError):
    pass


class StepHandlerRegistry:
    def __init__(self, handlers: list[WorkflowStepHandler] | None = None) -> None:
        self._handlers: dict[str, WorkflowStepHandler] = {}
        for handler in handlers or []:
            self.register(handler)

    def register(self, handler: WorkflowStepHandler) -> None:
        self._handlers[handler.name] = handler

    def get(self, name: str) -> WorkflowStepHandler:
        try:
            return self._handlers[name]
        except KeyError as exc:
            raise StepHandlerNotFoundError(f"Unknown workflow step handler: {name}") from exc


class SnapshotInputHandler:
    name = "snapshot_inputs"

    async def handle(self, context: WorkflowExecutionContext, step: WorkflowStepDefinition) -> WorkflowStepOutcome:
        include = step.parameters.get("include_keys")
        if isinstance(include, list):
            payload = {key: context.input_data.get(key) for key in include}
        else:
            payload = dict(context.input_data)

        output_key = step.parameters.get("output_key")
        if isinstance(output_key, str) and output_key:
            payload = {output_key: payload}

        return WorkflowStepOutcome.completed(output=payload, metadata={"handler": self.name})


class ApprovalGateHandler:
    name = "approval_gate"

    async def handle(self, context: WorkflowExecutionContext, step: WorkflowStepDefinition) -> WorkflowStepOutcome:
        approvals = context.input_data.get("approvals", {})
        approval_key = str(step.parameters.get("approval_key") or step.name)
        approved = False
        if isinstance(approvals, dict):
            approved = bool(approvals.get(approval_key, False))
        if approved:
            return WorkflowStepOutcome.completed(
                output={approval_key: {"approved": True}},
                metadata={"approval_key": approval_key, "approved": True},
            )
        return WorkflowStepOutcome(
            status=WorkflowStepStatus.AWAITING_APPROVAL,
            output={approval_key: {"approved": False}},
            metadata={"approval_key": approval_key, "approved": False},
        )


class SynthesizeSummaryHandler:
    name = "synthesize_summary"

    async def handle(self, context: WorkflowExecutionContext, step: WorkflowStepDefinition) -> WorkflowStepOutcome:
        summary_title = str(step.parameters.get("title") or context.definition.name)
        keys = step.parameters.get("include_keys")
        source = context.snapshot()
        if isinstance(keys, list):
            summary = {key: source["variables"].get(key, source["input"].get(key)) for key in keys}
        else:
            summary = {**source["input"], **source["variables"]}

        output_key = str(step.parameters.get("output_key") or "summary")
        return WorkflowStepOutcome.completed(
            output={output_key: {"title": summary_title, "details": summary}},
            metadata={"handler": self.name},
        )


class ServiceTaskHandler:
    name = "service_task"

    async def handle(self, context: WorkflowExecutionContext, step: WorkflowStepDefinition) -> WorkflowStepOutcome:
        service_name = step.parameters.get("service_name")
        if not isinstance(service_name, str) or not service_name:
            raise ValueError(f"Workflow step '{step.name}' is missing a service_name")
        service = context.services.get(service_name)
        if service is None:
            raise ValueError(f"Workflow service task '{service_name}' is not registered")

        result = service(context, step)
        if inspect.isawaitable(result):
            result = await result

        if isinstance(result, WorkflowStepOutcome):
            return result
        if not isinstance(result, dict):
            raise TypeError(f"Workflow service task '{service_name}' must return a dict or WorkflowStepOutcome")
        return WorkflowStepOutcome.completed(output=result, metadata={"service_name": service_name})