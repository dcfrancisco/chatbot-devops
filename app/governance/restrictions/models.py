from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class RestrictionViolation:
    code: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RestrictionSet:
    tool_execution_enabled: bool = True
    allowed_tools: tuple[str, ...] = ()
    blocked_tools: tuple[str, ...] = ()
    approval_required_tools: tuple[str, ...] = ()
    allowed_agents: tuple[str, ...] = ()
    max_message_chars: int | None = None

    def merge(self, other: RestrictionSet) -> RestrictionSet:
        return RestrictionSet(
            tool_execution_enabled=self.tool_execution_enabled and other.tool_execution_enabled,
            allowed_tools=self._merge_allowed(self.allowed_tools, other.allowed_tools),
            blocked_tools=self._merge_union(self.blocked_tools, other.blocked_tools),
            approval_required_tools=self._merge_union(self.approval_required_tools, other.approval_required_tools),
            allowed_agents=self._merge_allowed(self.allowed_agents, other.allowed_agents),
            max_message_chars=self._merge_max_chars(self.max_message_chars, other.max_message_chars),
        )

    def as_metadata(self) -> dict[str, object]:
        return {
            "tool_execution_enabled": self.tool_execution_enabled,
            "allowed_tools": list(self.allowed_tools),
            "blocked_tools": list(self.blocked_tools),
            "approval_required_tools": list(self.approval_required_tools),
            "allowed_agents": list(self.allowed_agents),
            "max_message_chars": self.max_message_chars,
        }

    def _merge_union(self, left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted({*left, *right}))

    def _merge_allowed(self, left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
        if left and right:
            return tuple(sorted(set(left).intersection(right)))
        if left:
            return left
        if right:
            return right
        return ()

    def _merge_max_chars(self, left: int | None, right: int | None) -> int | None:
        if left is None:
            return right
        if right is None:
            return left
        return min(left, right)