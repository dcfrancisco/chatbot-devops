from __future__ import annotations

import inspect
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar


class NamedComponent(Protocol):
    name: str


ComponentT = TypeVar("ComponentT", bound=NamedComponent)


@dataclass(slots=True, frozen=True)
class ComponentDescriptor:
    name: str
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RegistryEntry(Generic[ComponentT]):
    component: ComponentT
    descriptor: ComponentDescriptor


class ComponentNotFoundError(KeyError):
    pass


class NamedRegistry(Generic[ComponentT]):
    def __init__(self, items: Iterable[ComponentT] | None = None) -> None:
        self._items: dict[str, ComponentT] = {}
        self._descriptors: dict[str, ComponentDescriptor] = {}
        for item in items or []:
            self.register(item)

    def register(self, item: ComponentT) -> None:
        self._validate(item)
        if item.name in self._items:
            raise ValueError(f"Component already registered: {item.name}")
        self._items[item.name] = item
        self._descriptors[item.name] = self._build_descriptor(item)

    async def register_async(self, item: ComponentT) -> None:
        self.register(item)

    def list(self) -> list[ComponentT]:
        return [self._items[name] for name in sorted(self._items)]

    def entries(self) -> list[RegistryEntry[ComponentT]]:
        return [RegistryEntry(component=self._items[name], descriptor=self._descriptors[name]) for name in sorted(self._items)]

    def names(self) -> list[str]:
        return sorted(self._items)

    def get(self, name: str) -> ComponentT:
        try:
            return self._items[name]
        except KeyError as exc:
            raise ComponentNotFoundError(f"Unknown component: {name}") from exc

    def describe(self, name: str) -> ComponentDescriptor:
        try:
            return self._descriptors[name]
        except KeyError as exc:
            raise ComponentNotFoundError(f"Unknown component: {name}") from exc

    def discover(self, *, capability: str | None = None) -> list[RegistryEntry[ComponentT]]:
        if capability is None:
            return self.entries()
        return [entry for entry in self.entries() if capability in entry.descriptor.capabilities]

    async def aclose(self) -> None:
        for component in reversed(self.list()):
            close_method = getattr(component, "aclose", None)
            if close_method is None:
                continue
            result = close_method()
            if inspect.isawaitable(result):
                await result

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def _validate(self, item: ComponentT) -> None:
        if not getattr(item, "name", ""):
            raise ValueError("Registered components must define a non-empty 'name'")

    def _build_descriptor(self, item: ComponentT) -> ComponentDescriptor:
        metadata_method = getattr(item, "metadata", None)
        metadata: dict[str, Any] = {}
        if callable(metadata_method):
            raw = metadata_method()
            if isinstance(raw, dict):
                metadata = raw

        registered_metadata = getattr(item, "__registry_metadata__", None)
        if isinstance(registered_metadata, dict):
            metadata = {**registered_metadata, **metadata}

        capabilities = self._extract_capabilities(item, metadata)
        return ComponentDescriptor(name=item.name, capabilities=capabilities, metadata=metadata)

    def _extract_capabilities(self, item: ComponentT, metadata: dict[str, Any]) -> tuple[str, ...]:
        registered_capabilities = getattr(item, "__registry_capabilities__", None)
        if isinstance(registered_capabilities, tuple):
            return registered_capabilities
        if isinstance(registered_capabilities, list):
            return tuple(str(value) for value in registered_capabilities)

        raw = getattr(item, "capabilities", None)
        if isinstance(raw, tuple):
            return raw
        if isinstance(raw, list):
            return tuple(str(value) for value in raw)

        meta_capabilities = metadata.get("capabilities")
        if isinstance(meta_capabilities, tuple):
            return meta_capabilities
        if isinstance(meta_capabilities, list):
            return tuple(str(value) for value in meta_capabilities)

        tags = getattr(item, "tags", ())
        if isinstance(tags, tuple):
            return tags
        if isinstance(tags, list):
            return tuple(str(value) for value in tags)
        return ()