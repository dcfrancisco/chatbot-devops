from __future__ import annotations

from app.governance.interceptors.context import GovernanceTarget


TARGET_APPROVAL_EXAMPLES: dict[GovernanceTarget, dict[str, object]] = {
    GovernanceTarget.TOOL_EXECUTION: {"approval": "required for restricted or write-capable tools"},
    GovernanceTarget.WORKFLOW_EXECUTION: {"approval": "reserved for future long-running workflow approval gates"},
    GovernanceTarget.PROMPT_GENERATION: {"approval": "usually not required unless policy escalates"},
    GovernanceTarget.MEMORY_ACCESS: {"approval": "future actor-sensitive memory review gate"},
    GovernanceTarget.RETRIEVAL_ACCESS: {"approval": "future document-scope approval gate"},
}
