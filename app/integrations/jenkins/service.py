from typing import Any

import httpx

from app.core.config import Settings


class JenkinsServiceError(Exception):
    pass


class JenkinsService:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        timeout_seconds: float,
        verify_tls: bool,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            auth=(username, password),
            timeout=timeout_seconds,
            verify=verify_tls,
            headers={"Accept": "application/json"},
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "JenkinsService":
        return cls(
            base_url=settings.jenkins_base_url,
            username=settings.jenkins_username,
            password=settings.jenkins_password,
            timeout_seconds=settings.jenkins_timeout_seconds,
            verify_tls=settings.jenkins_verify_tls,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_jobs(self) -> dict[str, Any]:
        response = await self._client.get("/api/json", params={"tree": "jobs[name,url,color]"})
        if response.status_code >= 400:
            raise JenkinsServiceError(response.text)
        return response.json()

    async def get_job(self, *, name: str) -> dict[str, Any]:
        response = await self._client.get(f"/job/{name}/api/json")
        if response.status_code >= 400:
            raise JenkinsServiceError(response.text)
        return response.json()

    async def create_job(self, *, name: str, config_xml: str) -> dict[str, Any]:
        headers = {"Content-Type": "application/xml"}
        crumb = await self._get_crumb()
        if crumb is not None:
            crumb_header, crumb_value = crumb
            headers[crumb_header] = crumb_value
        response = await self._client.post(
            f"/createItem?name={name}",
            headers=headers,
            content=config_xml.encode("utf-8"),
        )
        if response.status_code not in {200, 201, 302}:
            raise JenkinsServiceError(response.text)
        return {"name": name, "created": True, "location": response.headers.get("Location")}

    async def _get_crumb(self) -> tuple[str, str] | None:
        response = await self._client.get("/crumbIssuer/api/json")
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise JenkinsServiceError(response.text)
        payload = response.json()
        return payload["crumbRequestField"], payload["crumb"]