from __future__ import annotations

from app.governance.interceptors.context import GovernanceTarget


TARGET_POLICY_EXAMPLES: dict[GovernanceTarget, dict[str, object]] = {
    GovernanceTarget.TOOL_EXECUTION: {"policy": "enforce tool allowlist and approvals"},
    GovernanceTarget.WORKFLOW_EXECUTION: {"policy": "enforce workflow allowlist and future workflow RBAC"},
    GovernanceTarget.PROMPT_GENERATION: {"policy": "enforce prompt safety and content limits"},
    GovernanceTarget.MEMORY_ACCESS: {"policy": "enforce scoped memory access and future actor restrictions"},
    GovernanceTarget.RETRIEVAL_ACCESS: {"policy": "enforce scoped retrieval access and future document controls"},
}
