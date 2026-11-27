"""The Corpus facade: the only public entry point into the module.

It embeds chunk texts on write and the search query on read (Voyage in live
mode, a deterministic fake in tests), then delegates persistence and vector
search to the ChunkStore port. Embeddings stay out of the store.
"""

from collections.abc import Sequence

from langchain_core.embeddings import Embeddings

from docqa.corpus.store import ChunkStore
from docqa.domain import Chunk, DocumentId, DocumentInfo, Passage, WorkspaceId


class Corpus:
    def __init__(self, store: ChunkStore, embeddings: Embeddings) -> None:
        self._store = store
        self._embeddings = embeddings

    def put_document(self, ws: WorkspaceId, info: DocumentInfo, chunks: Sequence[Chunk]) -> None:
        vectors = self._embeddings.embed_documents([c.text for c in chunks]) if chunks else []
        self._store.put_document(ws, info, chunks, vectors)

    def list_documents(self, ws: WorkspaceId) -> list[DocumentInfo]:
        return self._store.list_documents(ws)

    def find_document(self, ws: WorkspaceId, doc: DocumentId) -> DocumentInfo | None:
        return self._store.find_document(ws, doc)

    def delete_document(self, ws: WorkspaceId, doc: DocumentId) -> None:
        self._store.delete_document(ws, doc)

    def search(
        self,
        ws: WorkspaceId,
        query: str,
        *,
        k: int = 4,
        only: Sequence[DocumentId] | None = None,
    ) -> list[Passage]:
        embedding = self._embeddings.embed_query(query)
        return self._store.search(ws, embedding, k=k, only=only)
