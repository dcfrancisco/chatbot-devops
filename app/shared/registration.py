from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar


ComponentT = TypeVar("ComponentT")


@dataclass(slots=True, frozen=True)
class RegistrationSpec(Generic[ComponentT]):
    name: str
    factory: Callable[..., ComponentT]
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class FactoryCatalog(Generic[ComponentT]):
    def __init__(self) -> None:
        self._specs: dict[str, RegistrationSpec[ComponentT]] = {}

    def register(
        self,
        *,
        name: str,
        factory: Callable[..., ComponentT],
        capabilities: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not name:
            raise ValueError("Registered factories must define a non-empty name")
        if name in self._specs:
            raise ValueError(f"Factory already registered: {name}")
        self._specs[name] = RegistrationSpec(
            name=name,
            factory=factory,
            capabilities=capabilities,
            metadata=metadata or {},
        )

    def specs(self) -> list[RegistrationSpec[ComponentT]]:
        return [self._specs[name] for name in sorted(self._specs)]

    def build_all(self, **dependencies: Any) -> list[ComponentT]:
        return [self._build_one(spec, dependencies) for spec in self.specs()]

    def _build_one(self, spec: RegistrationSpec[ComponentT], dependencies: dict[str, Any]) -> ComponentT:
        signature = inspect.signature(spec.factory)
        accepted = {
            name: value
            for name, value in dependencies.items()
            if name in signature.parameters
        }
        component = spec.factory(**accepted)
        setattr(component, "__registry_capabilities__", spec.capabilities)
        setattr(component, "__registry_metadata__", spec.metadata)
        return component


def register_factory(
    catalog: FactoryCatalog[ComponentT],
    *,
    name: str,
    capabilities: tuple[str, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., ComponentT]], Callable[..., ComponentT]]:
    def decorator(factory: Callable[..., ComponentT]) -> Callable[..., ComponentT]:
        catalog.register(name=name, factory=factory, capabilities=capabilities, metadata=metadata)
        return factory

    return decorator