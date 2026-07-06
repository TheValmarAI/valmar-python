"""Valmar Python SDK client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from valmar.models import (
    ContextReference,
    ContextRequest,
    ContextRequestAssignment,
    ContextRequestHandle,
    ContextRequestListItem,
    ContextResource,
    ContextSearchResult,
    ContextTrace,
    CreateContextRequestInput,
    CreatePersonInput,
    ImportPeopleInput,
    ImportPeopleResult,
    KnowledgeGapsArtifact,
    KnowledgeGapsOverview,
    KnowledgeGapsPipelineRunInput,
    KnowledgeGapsPipelineRunStatus,
    KnowledgeGapsSubmission,
    KnowledgeGapsSubmitResponse,
    Person,
    SearchContextInput,
)

DEFAULT_TIMEOUT = 30.0


class _Resource:
    def __init__(self, client: Valmar) -> None:
        self._client = client

    @property
    def _http(self) -> httpx.Client:
        return self._client._http

    @property
    def _organization_id(self) -> UUID | None:
        return self._client.organization_id

    @property
    def _project_id(self) -> UUID | None:
        return self._client.project_id

    def _require_organization_id(self) -> UUID:
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client for this operation.")
        return self._organization_id

    def _require_project_id(self) -> UUID:
        if self._project_id is None:
            raise ValueError("project_id must be set on the client for this operation.")
        return self._project_id


class ContextResourceClient(_Resource):
    """Search and read project-scoped Context Hub resources."""

    def search(
        self,
        query: str = "",
        *,
        limit: int = 10,
        modules: list[str] | None = None,
        source_member_ids: list[UUID | str] | None = None,
    ) -> ContextSearchResult:
        payload = SearchContextInput(
            organization_id=self._require_organization_id(),
            project_id=self._require_project_id(),
            query=query,
            limit=limit,
            modules=modules or [],
            source_member_ids=[UUID(str(item)) for item in (source_member_ids or [])],
        )
        response = self._http.post("/api/context/search", json=payload.model_dump(mode="json"))
        response.raise_for_status()
        return ContextSearchResult.model_validate(response.json())

    def read(self, reference: ContextReference | str) -> ContextResource:
        module, resource_id = self._reference_parts(reference)
        response = self._http.get(f"/api/context/resources/{module}/{resource_id}")
        response.raise_for_status()
        return ContextResource.model_validate(response.json())

    def trace(self, reference: ContextReference | str) -> ContextTrace:
        module, resource_id = self._reference_parts(reference)
        response = self._http.get(f"/api/context/resources/{module}/{resource_id}/trace")
        response.raise_for_status()
        return ContextTrace.model_validate(response.json())

    def _reference_parts(self, reference: ContextReference | str) -> tuple[str, str]:
        uri = reference.uri if isinstance(reference, ContextReference) else reference
        prefix = "valmar://context/"
        if not uri.startswith(prefix):
            raise ValueError("reference must be a valmar://context URI.")
        parts = uri.removeprefix(prefix).split("/")
        if len(parts) != 3:
            raise ValueError("reference must include project, module, and resource identifiers.")
        project_id, module, resource_id = parts
        if UUID(project_id) != self._require_project_id():
            raise ValueError("reference belongs to a different project.")
        return module, resource_id


class ContextRequestsResource(_Resource):
    """Create and inspect human-routed context requests."""

    def create(
        self,
        question: str,
        *,
        already_tried: str | None = None,
        background_context: str | None = None,
        requesting_application: str = "valmar-sdk-python",
        source_agent_config_id: UUID | str | None = None,
    ) -> ContextRequestHandle:
        payload = CreateContextRequestInput(
            project_id=self._require_project_id(),
            requesting_application=requesting_application,
            question=question,
            already_tried=already_tried,
            background_context=background_context,
            source_agent_config_id=(
                UUID(str(source_agent_config_id)) if source_agent_config_id is not None else None
            ),
        )
        response = self._http.post(
            "/api/context/requests",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
        return ContextRequestHandle.model_validate(response.json())

    def get(self, context_request_id: UUID | str) -> ContextRequest:
        response = self._http.get(f"/api/context/requests/{context_request_id}")
        response.raise_for_status()
        return ContextRequest.model_validate(response.json())

    def list(self) -> list[ContextRequestListItem]:
        response = self._http.get(
            "/api/context/requests",
            params={"project_id": str(self._require_project_id())},
        )
        response.raise_for_status()
        return [ContextRequestListItem.model_validate(item) for item in response.json()]

    def list_assignments(
        self,
        knowledge_request_id: UUID | str,
    ) -> list[ContextRequestAssignment]:
        response = self._http.get(
            f"/api/context/requests/{knowledge_request_id}/assignments"
        )
        response.raise_for_status()
        return [ContextRequestAssignment.model_validate(item) for item in response.json()]

    def assign(
        self,
        knowledge_request_id: UUID | str,
        *,
        member_id: UUID | str,
        reason: str | None = None,
    ) -> ContextRequestAssignment:
        payload = {
            "member_id": str(member_id),
            "reason": reason,
        }
        response = self._http.post(
            f"/api/context/requests/{knowledge_request_id}/assignments",
            json=payload,
        )
        response.raise_for_status()
        return ContextRequestAssignment.model_validate(response.json())

class PeopleResource(_Resource):
    """Manage organization people that Valmar may contact."""

    def list(self) -> list[Person]:
        response = self._http.get(f"/api/organizations/{self._require_organization_id()}/people")
        response.raise_for_status()
        return [Person.model_validate(item) for item in response.json()]

    def import_bulk(self, people: list[CreatePersonInput]) -> ImportPeopleResult:
        payload = ImportPeopleInput(people=people)
        response = self._http.post(
            f"/api/organizations/{self._require_organization_id()}/people/import",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
        return ImportPeopleResult.model_validate(response.json())


class KnowledgeGapsResource(_Resource):
    """Run project-scoped proactive Knowledge Gap analysis."""

    def _base_path(self) -> str:
        return f"/api/projects/{self._require_project_id()}/knowledge-gaps"

    def overview(self) -> KnowledgeGapsOverview:
        response = self._http.get(f"{self._base_path()}/overview")
        response.raise_for_status()
        return KnowledgeGapsOverview.model_validate(response.json())

    def start_run(
        self, *, custom_instructions: str | None = None
    ) -> KnowledgeGapsPipelineRunStatus:
        payload = KnowledgeGapsPipelineRunInput(custom_instructions=custom_instructions)
        response = self._http.post(
            f"{self._base_path()}/run",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()
        return KnowledgeGapsPipelineRunStatus.model_validate(response.json())

    def get_run_artifact(self, run_id: UUID | str, name: str) -> KnowledgeGapsArtifact:
        response = self._http.get(f"{self._base_path()}/runs/{run_id}/artifacts/{name}")
        response.raise_for_status()
        return response.json()

    def submit_ranked_gaps(
        self,
        run_id: UUID | str,
        *,
        gap_ranks: list[int] | None = None,
    ) -> list[KnowledgeGapsSubmission]:
        response = self._http.post(
            f"{self._base_path()}/runs/{run_id}/submit",
            json={"gap_ranks": gap_ranks},
        )
        response.raise_for_status()
        return KnowledgeGapsSubmitResponse.model_validate(response.json()).submissions


class Valmar:
    """Small HTTP client for the Valmar REST API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str,
        organization_id: UUID | str | None = None,
        project_id: UUID | str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.organization_id: UUID | None = UUID(str(organization_id)) if organization_id else None
        self.project_id: UUID | None = UUID(str(project_id)) if project_id else None

        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "valmar-sdk-python/1.0.0",
            },
            timeout=timeout,
        )

        self.context = ContextResourceClient(self)
        self.context_requests = ContextRequestsResource(self)
        self.people = PeopleResource(self)
        self.knowledge_gaps = KnowledgeGapsResource(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Valmar:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
