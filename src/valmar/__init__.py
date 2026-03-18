"""Valmar Python SDK — thin httpx client with Pydantic models."""

from valmar.client import ValmarClient
from valmar.models import (
    BulkImportMemberResult,
    BulkImportMembersInput,
    BulkImportMembersResult,
    ContextPart,
    ContextPartProvenance,
    ContextPartType,
    ContextRequest,
    ContextRequestAnswer,
    ContextRequestHandle,
    ContextRequestResolutionStatus,
    ContextRequestStatus,
    ContextSearchResult,
    CreateContextRequestInput,
    CreateMemberInput,
    CreateWebhookEndpointInput,
    Member,
    ProjectRole,
    ReviewStatus,
    SearchContextInput,
    ThreadStatus,
    WebhookEndpoint,
)

__all__ = [
    "ValmarClient",
    # Models
    "BulkImportMemberResult",
    "BulkImportMembersInput",
    "BulkImportMembersResult",
    "ContextPart",
    "ContextPartProvenance",
    "ContextPartType",
    "ContextRequest",
    "ContextRequestAnswer",
    "ContextRequestHandle",
    "ContextRequestResolutionStatus",
    "ContextRequestStatus",
    "ContextSearchResult",
    "CreateContextRequestInput",
    "CreateMemberInput",
    "CreateWebhookEndpointInput",
    "Member",
    "ProjectRole",
    "ReviewStatus",
    "SearchContextInput",
    "ThreadStatus",
    "WebhookEndpoint",
]

__version__ = "0.1.0"
