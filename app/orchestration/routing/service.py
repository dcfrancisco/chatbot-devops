from app.orchestration.routing.interfaces import RequestRouter
from app.orchestration.state.models import ToolPlan
from app.rag.retriever import RetrievalResult


class DeterministicRequestRouter(RequestRouter):
    def route(self, user_message: str, retrieval: RetrievalResult) -> ToolPlan | None:
        lowered = user_message.lower()
        retrieval_is_thin = len(retrieval.citations) < 2

        if self._should_use_jenkins_tool(lowered, retrieval_is_thin):
            if "list" in lowered and "job" in lowered:
                return ToolPlan(name="jenkins", arguments={"action": "list_jobs"})
            if any(marker in lowered for marker in ("details for job", "job details", "show job")):
                job_name = self._extract_named_value(user_message, markers=["job", "named"])
                if job_name:
                    return ToolPlan(name="jenkins", arguments={"action": "get_job", "name": job_name})

        if self._should_use_api_tool(lowered):
            integration = self._extract_named_value(user_message, markers=["integration", "service"])
            path = self._extract_path(user_message)
            if integration and path:
                return ToolPlan(
                    name="api",
                    arguments={
                        "integration": integration,
                        "method": "GET",
                        "path": path,
                    },
                )

        return None

    def _should_use_jenkins_tool(self, lowered: str, retrieval_is_thin: bool) -> bool:
        return retrieval_is_thin and "jenkins" in lowered and any(
            marker in lowered for marker in ("list job", "list jobs", "show job", "job details")
        )

    def _should_use_api_tool(self, lowered: str) -> bool:
        return "api" in lowered and any(marker in lowered for marker in ("integration", "service", "path"))

    def _extract_named_value(self, text: str, markers: list[str]) -> str | None:
        words = text.replace("\n", " ").split()
        lowered_words = [word.lower().strip(":,.") for word in words]
        for index, word in enumerate(lowered_words):
            if word in markers and index + 1 < len(words):
                return words[index + 1].strip("\"' ,.")
        return None

    def _extract_path(self, text: str) -> str | None:
        for token in text.split():
            if token.startswith("/") and "://" not in token:
                return token.rstrip(".,")
        return None