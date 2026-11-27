"""Shared, frozen domain types. See docs/ARCHITECTURE.md and docs/GLOSSARY.md.

The server adds its own types in T5.
"""

from datetime import datetime
from typing import NewType

from pydantic import BaseModel, ConfigDict

WorkspaceId = NewType("WorkspaceId", str)  # UUID4 made in the browser
DocumentId = NewType("DocumentId", str)  # sha256(workspace_id + "/" + name)[:16]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Upload(_Frozen):
    """A file as received: its name, declared content type and raw bytes."""

    name: str
    content_type: str
    data: bytes


class DocumentInfo(_Frozen):
    """One row in the documents registry (ADR-0012)."""

    document_id: DocumentId
    name: str
    pages: int
    chunks: int
    content_hash: str
    uploaded_at: datetime


class Chunk(_Frozen):
    """Up to 1,500 characters of a document, before embedding. A row in chunks."""

    index: int
    text: str
    page: int | None
    start_index: int


class Passage(_Frozen):
    """A chunk returned by a search, with its cosine-similarity score."""

    document_id: DocumentId
    name: str
    page: int | None
    text: str
    score: float


class AskRequest(_Frozen):
    """A question for one workspace. thread_id continues a thread; None starts one."""

    workspace: WorkspaceId
    question: str
    thread_id: str | None = None
    document_ids: list[DocumentId] | None = None


class Citation(_Frozen):
    """Marker [n] in an answer, pointing at one passage."""

    n: int
    document_id: DocumentId
    name: str
    page: int | None
    snippet: str  # the first 200 characters of the passage, for display only


class Answer(_Frozen):
    """Either text whose every marker is a real citation, or the refusal."""

    thread_id: str
    text: str
    refused: bool
    citations: list[Citation]
