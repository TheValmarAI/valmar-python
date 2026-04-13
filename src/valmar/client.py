"""Valmar Python SDK client with namespace-based API access."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from valmar.models import (
    BulkImportMembersInput,
    BulkImportMembersResult,
    ContextPart,
    ContextRequest,
    ContextRequestHandle,
    ContextSearchResult,
    CreateContextRequestInput,
    CreateMemberInput,
    Member,
    SearchContextInput,
)

DEFAULT_BASE_URL = "https://api.valmar.dev"
DEFAULT_TIMEOUT = 30.0


class _Namespace:
    """Base class for API namespaces that share a common HTTP client."""

    def __init__(self, client: ValmarClient) -> None:
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


# ---------------------------------------------------------------------------
# Context namespace
# ---------------------------------------------------------------------------


class ContextNamespace(_Namespace):
    """Operations on context requests and context search."""

    def gather(
        self,
        question: str,
        *,
        already_tried: str | None = None,
        background_context: str | None = None,
        requesting_application: str = "valmar-sdk-python",
        source_agent_config_id: UUID | None = None,
    ) -> ContextRequestHandle:
        """Create a new context request (POST /api/context/requests).

        Returns a handle with the request ID and current status.
        """
        if self._project_id is None:
            raise ValueError("project_id must be set on the client to create context requests.")
        payload = CreateContextRequestInput(
            project_id=self._project_id,
            requesting_application=requesting_application,
            question=question,
            already_tried=already_tried,
            background_context=background_context,
            source_agent_config_id=source_agent_config_id,
        )
        resp = self._http.post("/api/context/requests", json=payload.model_dump(mode="json"))
        resp.raise_for_status()
        return ContextRequestHandle.model_validate(resp.json())

    def get(self, context_request_id: UUID) -> ContextRequest:
        """Retrieve a context request by ID (GET /api/context/requests/{id})."""
        resp = self._http.get(f"/api/context/requests/{context_request_id}")
        resp.raise_for_status()
        return ContextRequest.model_validate(resp.json())

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        types: list[str] | None = None,
        related_member_ids: list[UUID] | None = None,
    ) -> ContextSearchResult:
        """Search existing context parts (POST /api/context/search)."""
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to search context.")
        payload = SearchContextInput(
            organization_id=self._organization_id,
            project_id=self._project_id,
            query=query,
            limit=limit,
            types=types or [],
            related_member_ids=related_member_ids or [],
        )
        resp = self._http.post("/api/context/search", json=payload.model_dump(mode="json"))
        resp.raise_for_status()
        return ContextSearchResult.model_validate(resp.json())


# ---------------------------------------------------------------------------
# Knowledge namespace
# ---------------------------------------------------------------------------


class KnowledgeNamespace(_Namespace):
    """Read-only access to the knowledge base (context parts)."""

    def search(
        self,
        query: str,
        *,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> ContextSearchResult:
        """Search knowledge base entries (POST /api/context/search).

        Filters results by tags when provided.
        """
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to search knowledge.")
        payload = SearchContextInput(
            organization_id=self._organization_id,
            project_id=self._project_id,
            query=query,
            limit=limit,
        )
        resp = self._http.post("/api/context/search", json=payload.model_dump(mode="json"))
        resp.raise_for_status()
        result = ContextSearchResult.model_validate(resp.json())

        # Client-side tag filtering when tags are specified
        if tags:
            tag_set = set(tags)
            result.items = [
                item for item in result.items if tag_set & set(item.tags)
            ]
            result.total_count = len(result.items)

        return result


# ---------------------------------------------------------------------------
# People namespace
# ---------------------------------------------------------------------------


class PeopleNamespace(_Namespace):
    """People discovery operations."""

    def list(self) -> list[Member]:
        """List all members in the organization (GET /api/organizations/{org_id}/members)."""
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to list people.")
        resp = self._http.get(f"/api/organizations/{self._organization_id}/members")
        resp.raise_for_status()
        return [Member.model_validate(m) for m in resp.json()]

    def find_experts(self, topic: str) -> list[ContextPart]:
        """Find members with expertise on a topic.

        Searches context parts for member mentions related to the topic.
        Returns context parts whose related_member_ids are populated.
        """
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to find experts.")
        payload = SearchContextInput(
            organization_id=self._organization_id,
            project_id=self._project_id,
            query=topic,
            limit=20,
        )
        resp = self._http.post("/api/context/search", json=payload.model_dump(mode="json"))
        resp.raise_for_status()
        result = ContextSearchResult.model_validate(resp.json())
        return [part for part in result.items if part.related_member_ids]


# ---------------------------------------------------------------------------
# Members namespace
# ---------------------------------------------------------------------------


class MembersNamespace(_Namespace):
    """Member management operations."""

    def list(self) -> list[Member]:
        """List all members in the organization (GET /api/organizations/{org_id}/members)."""
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to list members.")
        resp = self._http.get(f"/api/organizations/{self._organization_id}/members")
        resp.raise_for_status()
        return [Member.model_validate(m) for m in resp.json()]

    def import_bulk(self, members: list[CreateMemberInput]) -> BulkImportMembersResult:
        """Bulk-import members (POST /api/organizations/{org_id}/members/import)."""
        if self._organization_id is None:
            raise ValueError("organization_id must be set on the client to import members.")
        payload = BulkImportMembersInput(members=members)
        resp = self._http.post(
            f"/api/organizations/{self._organization_id}/members/import",
            json=payload.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return BulkImportMembersResult.model_validate(resp.json())


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class ValmarClient:
    """Thin HTTP client for the Valmar REST API.

    Usage::

        from valmar import ValmarClient

        client = ValmarClient(
            api_key="valmr_proj_sk_...",
            organization_id="...",
            project_id="...",
        )
        result = client.context.search("deployment process")
    """

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

        # Namespaces
        self.context = ContextNamespace(self)
        self.knowledge = KnowledgeNamespace(self)
        self.people = PeopleNamespace(self)
        self.members = MembersNamespace(self)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> ValmarClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
