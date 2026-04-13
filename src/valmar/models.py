"""Pydantic models matching the Valmar backend API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ContextRequestStatus(StrEnum):
    PENDING = "pending"
    DEFERRED = "deferred"
    WAITING_FOR_REPLY = "waiting_for_reply"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class ContextRequestResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    PARTIAL_RESOLUTION = "partial_resolution"
    NOT_RESOLVED = "not_resolved"


class ContextPartType(StrEnum):
    TEXT = "text"


class ReviewStatus(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"


class ThreadStatus(StrEnum):
    OPEN = "open"
    WAITING_FOR_REPLY = "waiting_for_reply"
    CLOSED = "closed"


class ProjectRole(StrEnum):
    PROJECT_ADMIN = "project_admin"
    PROJECT_MEMBER = "project_member"
    SERVICE = "service"


# ---------------------------------------------------------------------------
# Shared value objects
# ---------------------------------------------------------------------------


class ContextPartProvenance(BaseModel):
    source_thread_id: UUID | None = None
    source_member_id: UUID | None = None
    source_agent_run_id: UUID | None = None
    source_context_request_id: UUID | None = None
    source_message_id: UUID | None = None


class ContextRequestAnswer(BaseModel):
    status: ContextRequestResolutionStatus
    answer_text: str
    answer_context_parts: list[UUID] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Domain models (responses)
# ---------------------------------------------------------------------------


class ContextPart(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organization_id: UUID
    project_id: UUID
    context_request_id: UUID | None = None
    type: ContextPartType
    title: str
    content_md: str
    provenance: ContextPartProvenance
    confidence: float = 0.65
    review_status: ReviewStatus = ReviewStatus.AUTO_ACCEPTED
    related_member_ids: list[UUID] = Field(default_factory=list)
    related_twin_node_ids: list[UUID] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ContextSearchResult(BaseModel):
    items: list[ContextPart] = Field(default_factory=list)
    total_count: int = 0


class ContextRequest(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organization_id: UUID
    project_id: UUID
    requesting_application: str
    question: str
    already_tried: str | None = None
    background_context: str | None = None
    candidate_member_ids: list[UUID] = Field(default_factory=list)
    status: ContextRequestStatus = ContextRequestStatus.PENDING
    source_agent_config_id: UUID | None = None
    response_deadline_at: datetime | None = None
    result_summary: str | None = None
    answer: ContextRequestAnswer | None = None
    resolved_thread_id: UUID | None = None
    created_by_actor_id: str


class ContextRequestHandle(BaseModel):
    context_request_id: UUID
    status: ContextRequestStatus
    resource_uri: str


class Member(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organization_id: UUID
    email: str
    display_name: str
    timezone: str = "UTC"
    title: str | None = None
    description_md: str = ""


# ---------------------------------------------------------------------------
# Input models (requests)
# ---------------------------------------------------------------------------


class CreateContextRequestInput(BaseModel):
    project_id: UUID
    requesting_application: str
    question: str
    already_tried: str | None = None
    background_context: str | None = None
    source_agent_config_id: UUID | None = None


class SearchContextInput(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    query: str = ""
    types: list[ContextPartType] = Field(default_factory=list)
    related_member_ids: list[UUID] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class CreateMemberInput(BaseModel):
    email: str
    display_name: str
    timezone: str = "UTC"
    title: str | None = None
    description_md: str = ""


class BulkImportMembersInput(BaseModel):
    members: list[CreateMemberInput]


class BulkImportMemberResult(BaseModel):
    email: str
    status: str
    member_id: UUID | None = None
    error: str | None = None


class BulkImportMembersResult(BaseModel):
    created: list[BulkImportMemberResult] = Field(default_factory=list)
    skipped: list[BulkImportMemberResult] = Field(default_factory=list)
    errors: list[BulkImportMemberResult] = Field(default_factory=list)
