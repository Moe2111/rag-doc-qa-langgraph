"""Shared, frozen domain types. See docs/ARCHITECTURE.md and docs/GLOSSARY.md.

Only the types the corpus needs live here so far; library, answering and the
server add theirs in T3-T5.
"""

from datetime import datetime
from typing import NewType

from pydantic import BaseModel, ConfigDict

WorkspaceId = NewType("WorkspaceId", str)  # UUID4 made in the browser
DocumentId = NewType("DocumentId", str)  # sha256(workspace_id + "/" + name)[:16]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


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
