from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import Settings


class ApiServiceError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class ApiIntegration:
    name: str
    base_url: str
    allowed_methods: tuple[str, ...] = ("GET",)
    allowed_paths: tuple[str, ...] = ("/",)
    timeout_seconds: float = 10.0
    default_headers: dict[str, str] = field(default_factory=dict)


class ApiService:
    def __init__(self, integrations: dict[str, ApiIntegration]) -> None:
        self._integrations = integrations
        self._clients = {
            name: httpx.AsyncClient(
                base_url=integration.base_url.rstrip("/"),
                timeout=integration.timeout_seconds,
                headers={"Accept": "application/json", **integration.default_headers},
            )
            for name, integration in integrations.items()
        }

    @classmethod
    def from_settings(cls, settings: Settings) -> "ApiService":
        raw = json.loads(settings.tool_api_integrations_json or "{}")
        integrations: dict[str, ApiIntegration] = {}
        for name, payload in raw.items():
            integrations[name] = ApiIntegration(
                name=name,
                base_url=str(payload["base_url"]),
                allowed_methods=tuple(str(method).upper() for method in payload.get("allowed_methods", ["GET"])),
                allowed_paths=tuple(str(path) for path in payload.get("allowed_paths", ["/"])),
                timeout_seconds=float(payload.get("timeout_seconds", settings.tool_execution_timeout_seconds)),
                default_headers={
                    str(header): str(value)
                    for header, value in payload.get("default_headers", {}).items()
                },
            )
        return cls(integrations)

    async def aclose(self) -> None:
        for client in self._clients.values():
            await client.aclose()

    def list_integrations(self) -> list[dict[str, Any]]:
        return [
            {
                "name": integration.name,
                "base_url": integration.base_url,
                "allowed_methods": list(integration.allowed_methods),
                "allowed_paths": list(integration.allowed_paths),
                "timeout_seconds": integration.timeout_seconds,
            }
            for integration in self._integrations.values()
        ]

    async def request(
        self,
        *,
        integration_name: str,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        integration = self._integrations.get(integration_name)
        if integration is None:
            raise ApiServiceError(f"Unknown API integration: {integration_name}")

        normalized_method = method.upper()
        if normalized_method not in integration.allowed_methods:
            raise ApiServiceError(f"Method {normalized_method} is not allowed for integration {integration_name}")
        if not path.startswith("/") or "://" in path:
            raise ApiServiceError("Only relative paths starting with '/' are allowed")
        if not any(path.startswith(prefix) for prefix in integration.allowed_paths):
            raise ApiServiceError(f"Path {path} is not allowed for integration {integration_name}")

        sanitized_headers: dict[str, str] = {}
        for header_name, header_value in (headers or {}).items():
            normalized_name = header_name.lower()
            if normalized_name in {"accept", "content-type", "x-request-id", "x-correlation-id"} or normalized_name.startswith("x-"):
                sanitized_headers[header_name] = header_value
            else:
                raise ApiServiceError(f"Header {header_name} is not allowed")

        response = await self._clients[integration_name].request(
            normalized_method,
            path,
            params=query,
            json=json_body,
            headers=sanitized_headers or None,
        )
        content_type = response.headers.get("content-type", "")
        body: Any
        if "application/json" in content_type:
            body = response.json()
        else:
            body = response.text

        return {
            "integration": integration_name,
            "method": normalized_method,
            "path": path,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }