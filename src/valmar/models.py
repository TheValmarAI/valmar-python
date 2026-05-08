"""Pydantic models for the Valmar Python SDK."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValmarModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class KnowledgeRequestStatus(StrEnum):
    PENDING = "pending"
    DEFERRED = "deferred"
    WAITING_FOR_REPLY = "waiting_for_reply"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class KnowledgeRequestResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    PARTIAL_RESOLUTION = "partial_resolution"
    NOT_RESOLVED = "not_resolved"


class KnowledgeItemType(StrEnum):
    TEXT = "text"


class ReviewStatus(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"


class ProjectRole(StrEnum):
    PROJECT_ADMIN = "project_admin"
    PROJECT_MEMBER = "project_member"
    SERVICE = "service"


class KnowledgeItemProvenance(ValmarModel):
    source_thread_id: UUID | None = None
    source_member_id: UUID | None = None
    source_agent_run_id: UUID | None = None
    source_knowledge_request_id: UUID | None = Field(
        default=None,
        validation_alias="source_knowledge_request_id",
        serialization_alias="source_knowledge_request_id",
    )
    source_message_id: UUID | None = None


class KnowledgeRequestAnswer(ValmarModel):
    status: KnowledgeRequestResolutionStatus
    answer_text: str
    answer_knowledge_items: list[UUID] = Field(
        default_factory=list,
        validation_alias="answer_knowledge_items",
        serialization_alias="answer_knowledge_items",
    )


class KnowledgeItem(ValmarModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organization_id: UUID
    project_id: UUID
    knowledge_request_id: UUID | None = Field(
        default=None,
        validation_alias="knowledge_request_id",
        serialization_alias="knowledge_request_id",
    )
    type: KnowledgeItemType
    title: str
    content_md: str
    provenance: KnowledgeItemProvenance
    confidence: float = 0.65
    review_status: ReviewStatus = ReviewStatus.AUTO_ACCEPTED
    related_member_ids: list[UUID] = Field(default_factory=list)
    related_twin_node_ids: list[UUID] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeSearchResult(ValmarModel):
    items: list[KnowledgeItem] = Field(default_factory=list)
    total_count: int = 0


class KnowledgeRequest(ValmarModel):
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
    status: KnowledgeRequestStatus = KnowledgeRequestStatus.PENDING
    source_agent_config_id: UUID | None = None
    response_deadline_at: datetime | None = None
    result_summary: str | None = None
    answer: KnowledgeRequestAnswer | None = None
    resolved_thread_id: UUID | None = None
    created_by_actor_id: str | None = None


class KnowledgeRequestListItem(ValmarModel):
    id: UUID
    project_id: UUID
    requesting_application: str
    question: str
    status: KnowledgeRequestStatus
    result_summary: str | None = None
    created_at: datetime
    assigned_member_id: UUID | None = None
    assigned_member_display_name: str | None = None


class KnowledgeRequestHandle(ValmarModel):
    knowledge_request_id: UUID = Field(
        validation_alias="knowledge_request_id",
        serialization_alias="knowledge_request_id",
    )
    status: KnowledgeRequestStatus
    resource_uri: str
    message: str


class Person(ValmarModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organization_id: UUID
    email: str
    display_name: str
    timezone: str = "UTC"
    title: str | None = None
    description_md: str = ""


class CreateKnowledgeRequestInput(ValmarModel):
    project_id: UUID
    requesting_application: str
    question: str
    already_tried: str | None = None
    background_context: str | None = None
    source_agent_config_id: UUID | None = None


class SearchKnowledgeInput(ValmarModel):
    organization_id: UUID
    project_id: UUID
    query: str = ""
    types: list[KnowledgeItemType] = Field(default_factory=list)
    related_member_ids: list[UUID] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class CreatePersonInput(ValmarModel):
    email: str
    display_name: str
    timezone: str = "UTC"
    title: str | None = None
    description_md: str = ""


class ImportPeopleInput(ValmarModel):
    people: list[CreatePersonInput]


class ImportPersonResult(ValmarModel):
    email: str
    status: str
    member_id: UUID | None = None
    error: str | None = None


class ImportPeopleResult(ValmarModel):
    created: list[ImportPersonResult] = Field(default_factory=list)
    skipped: list[ImportPersonResult] = Field(default_factory=list)
    errors: list[ImportPersonResult] = Field(default_factory=list)
