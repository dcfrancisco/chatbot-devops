from __future__ import annotations

from importlib import import_module


def load_registration_modules() -> None:
    for module_name in (
        "app.agents.registrations",
        "app.governance.registrations",
        "app.knowledge.registrations",
        "app.llm.registrations",
        "app.tools.registrations",
        "app.workflows.registrations",
    ):
        import_module(module_name)