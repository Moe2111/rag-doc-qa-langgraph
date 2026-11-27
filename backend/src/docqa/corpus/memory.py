"""In-memory ChunkStore: Python dicts and cosine similarity. For tests and
DOCQA_ADAPTERS=memory. Mirrors the Postgres adapter's behaviour exactly."""

import math
from collections.abc import Sequence

from docqa.domain import Chunk, DocumentId, DocumentInfo, Passage, WorkspaceId


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class MemoryChunkStore:
    def __init__(self) -> None:
        self._docs: dict[WorkspaceId, dict[DocumentId, DocumentInfo]] = {}
        self._chunks: dict[tuple[WorkspaceId, DocumentId], list[tuple[Chunk, list[float]]]] = {}

    def put_document(
        self,
        ws: WorkspaceId,
        info: DocumentInfo,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        self._docs.setdefault(ws, {})[info.document_id] = info
        self._chunks[(ws, info.document_id)] = [
            (chunk, list(vector)) for chunk, vector in zip(chunks, embeddings, strict=True)
        ]

    def list_documents(self, ws: WorkspaceId) -> list[DocumentInfo]:
        docs = self._docs.get(ws, {}).values()
        return sorted(docs, key=lambda d: (d.uploaded_at, d.document_id))

    def find_document(self, ws: WorkspaceId, doc: DocumentId) -> DocumentInfo | None:
        return self._docs.get(ws, {}).get(doc)

    def delete_document(self, ws: WorkspaceId, doc: DocumentId) -> None:
        self._docs.get(ws, {}).pop(doc, None)
        self._chunks.pop((ws, doc), None)

    def search(
        self,
        ws: WorkspaceId,
        embedding: Sequence[float],
        *,
        k: int,
        only: Sequence[DocumentId] | None,
    ) -> list[Passage]:
        allowed = set(only) if only is not None else None
        scored: list[tuple[float, DocumentInfo, Chunk]] = []
        for (w, doc), items in self._chunks.items():
            if w != ws or (allowed is not None and doc not in allowed):
                continue
            info = self._docs[ws][doc]
            for chunk, vector in items:
                scored.append((_cosine(embedding, vector), info, chunk))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            Passage(
                document_id=info.document_id,
                name=info.name,
                page=chunk.page,
                text=chunk.text,
                score=score,
            )
            for score, info, chunk in scored[:k]
        ]
