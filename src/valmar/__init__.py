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
    Member,
    ProjectRole,
    ReviewStatus,
    SearchContextInput,
    ThreadStatus,
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
    "Member",
    "ProjectRole",
    "ReviewStatus",
    "SearchContextInput",
    "ThreadStatus",
]

__version__ = "0.1.0"
