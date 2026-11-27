"""The ChunkStore port: persistence and workspace-scoped vector search.

The store never embeds. The Corpus facade embeds chunk texts and the search
query, then hands the vectors to the store. Both adapters (memory, Postgres)
must behave identically; the contract suite proves it (ADR-0008, ADR-0014).
"""

from collections.abc import Sequence
from typing import Protocol

from docqa.domain import Chunk, DocumentId, DocumentInfo, Passage, WorkspaceId


class ChunkStore(Protocol):
    def put_document(
        self,
        ws: WorkspaceId,
        info: DocumentInfo,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """Replace the document row and all of its chunks in one transaction."""
        ...

    def list_documents(self, ws: WorkspaceId) -> list[DocumentInfo]: ...

    def find_document(self, ws: WorkspaceId, doc: DocumentId) -> DocumentInfo | None: ...

    def delete_document(self, ws: WorkspaceId, doc: DocumentId) -> None: ...

    def search(
        self,
        ws: WorkspaceId,
        embedding: Sequence[float],
        *,
        k: int,
        only: Sequence[DocumentId] | None,
    ) -> list[Passage]:
        """The k nearest chunks by cosine similarity, highest score first."""
        ...
