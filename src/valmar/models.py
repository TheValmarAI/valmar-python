"""Pydantic models for the Valmar Python SDK."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
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


ContextProvenance = KnowledgeItemProvenance
ContextMetadata = KnowledgeItemMetadata


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


class ContextReference(ValmarModel):
    project_id: UUID
    module: str
    resource_id: UUID
    uri: str


class ContextResource(ValmarModel):
    reference: ContextReference
    title: str
    content_md: str
    provenance: KnowledgeItemProvenance
    review_status: ReviewStatus
    confidence: float
    source_member_ids: list[UUID] = Field(default_factory=list)
    source_thread_id: UUID | None = None
    source_context_request_id: UUID | None = None
    metadata: KnowledgeItemMetadata | None = None
    created_at: datetime
    updated_at: datetime


class ContextSearchHit(ValmarModel):
    reference: ContextReference
    title: str
    excerpt: str
    score: float
    source_member_ids: list[UUID] = Field(default_factory=list)
    source_thread_id: UUID | None = None
    source_context_request_id: UUID | None = None
    metadata: KnowledgeItemMetadata | None = None
    created_at: datetime


class ContextSearchResult(ValmarModel):
    hits: list[ContextSearchHit] = Field(default_factory=list)
    searched_modules: list[str] = Field(default_factory=list)


class ContextTraceMessage(ValmarModel):
    id: str
    role: str
    parts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: Any = None


class ContextTraceConversation(ValmarModel):
    thread_id: UUID
    member_id: UUID | None = None
    member_display_name: str | None = None
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[ContextTraceMessage] = Field(default_factory=list)


class ContextTraceEvent(ValmarModel):
    event_type: str
    title: str
    summary: str
    timestamp: datetime | None = None
    actor_label: str | None = None
    member_id: UUID | None = None
    member_display_name: str | None = None
    resource_id: UUID | None = None
    source_request_id: UUID | None = None
    assignment_id: UUID | None = None
    conversation_thread_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextTrace(ValmarModel):
    reference: ContextReference
    resource: ContextResource
    source_thread_ids: list[UUID] = Field(default_factory=list)
    conversations: dict[UUID, ContextTraceConversation] = Field(default_factory=dict)
    history: list[ContextTraceEvent] = Field(default_factory=list)
    audit_events: list[dict[str, Any]] = Field(default_factory=list)
    module_details: dict[str, Any] = Field(default_factory=dict)


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


class ContextRequestHandle(ValmarModel):
    context_request_id: UUID
    status: KnowledgeRequestStatus
    resource_uri: str
    message: str
    filter_decision: KnowledgeRequestFilterDecision | None = None


ContextRequest = KnowledgeRequest
ContextRequestAnswer = KnowledgeRequestAnswer
ContextRequestAssignment = KnowledgeRequestAssignment
ContextRequestAssignmentStatus = KnowledgeRequestAssignmentStatus
ContextRequestFilterDecision = KnowledgeRequestFilterDecision
ContextRequestListItem = KnowledgeRequestListItem
ContextRequestResolutionStatus = KnowledgeRequestResolutionStatus
ContextRequestStatus = KnowledgeRequestStatus


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


CreateContextRequestInput = CreateKnowledgeRequestInput


class SearchContextInput(ValmarModel):
    organization_id: UUID
    project_id: UUID
    query: str = ""
    modules: list[str] = Field(default_factory=list)
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


class KnowledgeGapsPipelineRunInput(ValmarModel):
    custom_instructions: str | None = None


class KnowledgeGapsPipelineRunStatus(ValmarModel):
    run_id: UUID
    status: Literal["idle", "running", "completed", "failed"]
    current_step: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class KnowledgeGapsArtifactOverview(ValmarModel):
    name: str
    filename: str
    exists: bool
    updated_at: datetime | None = None
    summary: list[str] = Field(default_factory=list)


class KnowledgeGapsSubmission(ValmarModel):
    gap_rank: int
    gap_title: str
    knowledge_request_id: UUID
    submitted_at: datetime
    submitted_by_actor_id: str | None = None


class KnowledgeGapsDismissal(ValmarModel):
    gap_rank: int
    gap_title: str
    reason: str | None = None
    dismissed_at: datetime
    dismissed_by_actor_id: str | None = None


class KnowledgeGapsConnection(ValmarModel):
    id: UUID
    name: str
    target_url: str | None = None
    target_api_key_set: bool = False
    chatbot_background_info: str | None = None
    custom_instructions: str | None = None
    target_message_field: str = "message"
    target_response_field: str = "response"
    target_supports_history: bool = False
    target_history_field: str = "messages"
    created_at: datetime
    updated_at: datetime


class KnowledgeGapsPipelineRunSummary(KnowledgeGapsPipelineRunStatus):
    connection_id: UUID | None = None
    connection_name: str | None = None
    artifacts: list[KnowledgeGapsArtifactOverview] = Field(default_factory=list)
    submissions: list[KnowledgeGapsSubmission] = Field(default_factory=list)
    dismissals: list[KnowledgeGapsDismissal] = Field(default_factory=list)
    ranked_gaps_count: int | None = None


class KnowledgeGapsConfigFieldStatus(ValmarModel):
    name: str
    label: str
    provided: bool
    required_for: str


class KnowledgeGapsConfigValues(ValmarModel):
    target_url: str | None = None
    target_api_key_set: bool = False
    chatbot_background_info: str | None = None
    custom_instructions: str | None = None
    target_message_field: str = "message"
    target_response_field: str = "response"
    target_supports_history: bool = False
    target_history_field: str = "messages"


class KnowledgeGapsOverview(ValmarModel):
    cli_command: str
    output_dir: str
    pipeline_ready: bool
    submission_ready: bool
    active_connection_id: UUID | None = None
    saved_connections: list[KnowledgeGapsConnection] = Field(default_factory=list)
    config_fields: list[KnowledgeGapsConfigFieldStatus] = Field(default_factory=list)
    artifacts: list[KnowledgeGapsArtifactOverview] = Field(default_factory=list)
    runs: list[KnowledgeGapsPipelineRunSummary] = Field(default_factory=list)
    run_status: KnowledgeGapsPipelineRunStatus | None = None
    config_values: KnowledgeGapsConfigValues | None = None


class KnowledgeGapsSubmitResponse(ValmarModel):
    submissions: list[KnowledgeGapsSubmission] = Field(default_factory=list)


KnowledgeGapsArtifact = dict[str, Any]
