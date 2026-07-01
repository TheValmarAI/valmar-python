"""Pydantic models for the Valmar Python SDK."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValmarModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class KnowledgeRequestStatus(StrEnum):
    PENDING = "pending"
    UNASSIGNED = "unassigned"
    DEFERRED = "deferred"
    WAITING_FOR_REPLY = "waiting_for_reply"
    WAITING_FOR_REVIEW = "waiting_for_review"
    COMPLETED = "completed"
    FILTERED_OUT = "filtered_out"
    DELETED = "deleted"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class KnowledgeRequestAssignmentStatus(StrEnum):
    PENDING = "pending"
    DEFERRED = "deferred"
    WAITING_FOR_REPLY = "waiting_for_reply"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class KnowledgeRequestResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_RESOLVED = "not_resolved"


class KnowledgeItemType(StrEnum):
    TEXT = "text"


class ReviewStatus(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"
    IGNORED = "ignored"


class ProjectRole(StrEnum):
    PROJECT_ADMIN = "project_admin"
    PROJECT_MEMBER = "project_member"
    SERVICE = "service"


class KnowledgeItemProvenance(ValmarModel):
    source_agent_run_id: UUID | None = None
    source_knowledge_request_id: UUID | None = Field(
        default=None,
        validation_alias="source_knowledge_request_id",
        serialization_alias="source_knowledge_request_id",
    )


class KnowledgeItemChatParticipant(ValmarModel):
    member_id: UUID
    display_name: str
    email: str
    title: str | None = None


class KnowledgeItemMetadata(ValmarModel):
    expert_names: list[str] = Field(default_factory=list)
    chat_participants: list[KnowledgeItemChatParticipant] = Field(default_factory=list)
    approved_at: datetime | None = None


class KnowledgeRequestAnswer(ValmarModel):
    status: KnowledgeRequestResolutionStatus
    answer_text: str
    answer_knowledge_items: list[UUID] = Field(
        default_factory=list,
        validation_alias="answer_knowledge_items",
        serialization_alias="answer_knowledge_items",
    )
    source_member_ids: list[UUID] = Field(default_factory=list)


class KnowledgeRequestFilterDecision(ValmarModel):
    decision: Literal["approved", "rejected"]
    reason: str
    matching_knowledge_request_ids: list[UUID] = Field(
        default_factory=list,
        validation_alias="matching_knowledge_request_ids",
        serialization_alias="matching_knowledge_request_ids",
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
    knowledge_request_assignment_id: UUID | None = None
    type: KnowledgeItemType
    title: str
    content_md: str
    metadata: KnowledgeItemMetadata | None = None
    provenance: KnowledgeItemProvenance
    source_thread_id: UUID | None = None
    confidence: float = 0.65
    review_status: ReviewStatus = ReviewStatus.AUTO_ACCEPTED
    source_member_ids: list[UUID] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeSearchResult(ValmarModel):
    items: list[KnowledgeItem] = Field(default_factory=list)
    total_count: int = 0


class KnowledgeRequestAssignedMember(ValmarModel):
    member_id: UUID
    display_name: str
    status: KnowledgeRequestAssignmentStatus


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
    filter_decision: KnowledgeRequestFilterDecision | None = None
    resolved_thread_id: UUID | None = None
    created_by_actor_id: str | None = None
    assigned_members: list[KnowledgeRequestAssignedMember] = Field(default_factory=list)


class KnowledgeRequestAssignment(ValmarModel):
    id: UUID
    knowledge_request_id: UUID
    member_id: UUID
    member_display_name: str
    member_title: str | None = None
    reason: str = ""
    score: float = 0.5
    evidence: list[dict] = Field(default_factory=list)
    status: KnowledgeRequestAssignmentStatus
    agent_run_id: UUID | None = None
    conversation_thread_id: UUID | None = None
    answer: KnowledgeRequestAnswer | None = None
    result_summary: str | None = None
    completed_at: datetime | None = None
    created_at: datetime


class KnowledgeRequestListItem(ValmarModel):
    id: UUID
    project_id: UUID
    requesting_application: str
    question: str
    status: KnowledgeRequestStatus
    result_summary: str | None = None
    filter_decision: KnowledgeRequestFilterDecision | None = None
    created_at: datetime
    assigned_members: list[KnowledgeRequestAssignedMember] = Field(default_factory=list)


class KnowledgeRequestHandle(ValmarModel):
    knowledge_request_id: UUID = Field(
        validation_alias="knowledge_request_id",
        serialization_alias="knowledge_request_id",
    )
    status: KnowledgeRequestStatus
    resource_uri: str
    message: str
    filter_decision: KnowledgeRequestFilterDecision | None = None


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
    source_member_ids: list[UUID] = Field(default_factory=list)
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
