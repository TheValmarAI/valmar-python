"""Valmar Python SDK client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from valmar.models import (
    CreateKnowledgeRequestInput,
    CreatePersonInput,
    ImportPeopleInput,
    ImportPeopleResult,
    KnowledgeItemType,
    KnowledgeRequest,
    KnowledgeRequestHandle,
    KnowledgeRequestListItem,
    KnowledgeSearchResult,
    Person,
    SearchKnowledgeInput,
)

DEFAULT_BASE_URL = "https://api.valmar.dev"
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


class KnowledgeResource(_Resource):
    """Search project-scoped knowledge saved by Valmar."""

    def search(
        self,
        query: str = "",
        *,
        limit: int = 10,
        types: list[KnowledgeItemType | str] | None = None,
        related_member_ids: list[UUID | str] | None = None,
    ) -> KnowledgeSearchResult:
        payload = SearchKnowledgeInput(
            organization_id=self._require_organization_id(),
            project_id=self._require_project_id(),
            query=query,
            limit=limit,
            types=[KnowledgeItemType(item) for item in (types or [])],
            related_member_ids=[UUID(str(item)) for item in (related_member_ids or [])],
        )
        response = self._http.post("/api/context/search", json=payload.model_dump(mode="json"))
        response.raise_for_status()
        return KnowledgeSearchResult.model_validate(response.json())


class KnowledgeRequestsResource(_Resource):
    """Create and inspect human-routed knowledge requests."""

    def create(
        self,
        question: str,
        *,
        already_tried: str | None = None,
        background_context: str | None = None,
        requesting_application: str = "valmar-sdk-python",
        source_agent_config_id: UUID | str | None = None,
    ) -> KnowledgeRequestHandle:
        payload = CreateKnowledgeRequestInput(
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
        return KnowledgeRequestHandle.model_validate(response.json())

    def get(self, knowledge_request_id: UUID | str) -> KnowledgeRequest:
        response = self._http.get(f"/api/context/requests/{knowledge_request_id}")
        response.raise_for_status()
        return KnowledgeRequest.model_validate(response.json())

    def list(self) -> list[KnowledgeRequestListItem]:
        response = self._http.get(
            f"/api/projects/{self._require_project_id()}/context-requests",
        )
        response.raise_for_status()
        return [KnowledgeRequestListItem.model_validate(item) for item in response.json()]


class PeopleResource(_Resource):
    """Manage organization people that Valmar may contact."""

    def list(self) -> list[Person]:
        response = self._http.get(f"/api/organizations/{self._require_organization_id()}/members")
        response.raise_for_status()
        return [Person.model_validate(item) for item in response.json()]

    def import_bulk(self, people: list[CreatePersonInput]) -> ImportPeopleResult:
        payload = ImportPeopleInput(members=people)
        response = self._http.post(
            f"/api/organizations/{self._require_organization_id()}/members/import",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
        return ImportPeopleResult.model_validate(response.json())


class Valmar:
    """Small HTTP client for the Valmar REST API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
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
                "User-Agent": "valmar-sdk-python/0.1.0",
            },
            timeout=timeout,
        )

        self.knowledge = KnowledgeResource(self)
        self.knowledge_requests = KnowledgeRequestsResource(self)
        self.people = PeopleResource(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Valmar:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
