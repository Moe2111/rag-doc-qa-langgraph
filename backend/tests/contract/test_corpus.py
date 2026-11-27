"""Corpus contract suite. Each test runs against both ChunkStore adapters so the
Postgres adapter is proven to behave exactly like the in-memory one. The
postgres parameter is marked so `-m "not postgres"` skips it without a database.
"""

import hashlib
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from docqa.corpus import Corpus, MemoryChunkStore, PostgresChunkStore
from docqa.domain import Chunk, DocumentId, DocumentInfo, WorkspaceId


@pytest.fixture(
    params=[
        pytest.param("memory"),
        pytest.param("postgres", marks=pytest.mark.postgres),
    ]
)
def corpus(request: pytest.FixtureRequest) -> Iterator[Corpus]:
    embeddings = DeterministicFakeEmbedding(size=512)
    if request.param == "memory":
        yield Corpus(MemoryChunkStore(), embeddings)
        return
    url: str = request.getfixturevalue("database_url")
    store = PostgresChunkStore.connect(url)
    try:
        yield Corpus(store, embeddings)
    finally:
        store.close()


def _ws() -> WorkspaceId:
    """A fresh workspace per test: isolation makes cleanup between tests unnecessary."""
    return WorkspaceId(str(uuid4()))


def _doc(ws: WorkspaceId, name: str, texts: Sequence[str]) -> tuple[DocumentInfo, list[Chunk]]:
    document_id = DocumentId(hashlib.sha256(f"{ws}/{name}".encode()).hexdigest()[:16])
    chunks = [
        Chunk(index=i, text=text, page=i + 1, start_index=i * 1500) for i, text in enumerate(texts)
    ]
    info = DocumentInfo(
        document_id=document_id,
        name=name,
        pages=len(texts),
        chunks=len(chunks),
        content_hash=hashlib.sha256("".join(texts).encode()).hexdigest(),
        uploaded_at=datetime.now(UTC),
    )
    return info, chunks


def test_add_then_search_returns_the_matching_chunk(corpus: Corpus) -> None:
    ws = _ws()
    info, chunks = _doc(ws, "nist.txt", ["alpha passage", "beta passage"])
    corpus.put_document(ws, info, chunks)

    hits = corpus.search(ws, "alpha passage")

    assert hits[0].text == "alpha passage"
    assert hits[0].document_id == info.document_id
    assert hits[0].score == pytest.approx(1.0)


def test_search_can_be_limited_to_one_document(corpus: Corpus) -> None:
    ws = _ws()
    keep, keep_chunks = _doc(ws, "keep.txt", ["shared term one"])
    other, other_chunks = _doc(ws, "other.txt", ["shared term two"])
    corpus.put_document(ws, keep, keep_chunks)
    corpus.put_document(ws, other, other_chunks)

    hits = corpus.search(ws, "shared term two", only=[keep.document_id])

    assert {h.document_id for h in hits} == {keep.document_id}


def test_delete_removes_the_document_and_its_chunks(corpus: Corpus) -> None:
    ws = _ws()
    info, chunks = _doc(ws, "gone.txt", ["findable passage"])
    corpus.put_document(ws, info, chunks)

    corpus.delete_document(ws, info.document_id)

    assert corpus.find_document(ws, info.document_id) is None
    assert corpus.search(ws, "findable passage") == []


def test_reupload_replaces_every_old_chunk(corpus: Corpus) -> None:
    ws = _ws()
    first, first_chunks = _doc(ws, "doc.txt", ["old one", "old two", "old three"])
    corpus.put_document(ws, first, first_chunks)
    second, second_chunks = _doc(ws, "doc.txt", ["fresh only"])
    corpus.put_document(ws, second, second_chunks)

    assert second.document_id == first.document_id  # same name in the same workspace
    listed = corpus.list_documents(ws)
    assert len(listed) == 1
    assert listed[0].chunks == 1
    assert {h.text for h in corpus.search(ws, "old two", k=10)} == {"fresh only"}


def test_workspace_b_never_sees_workspace_a(corpus: Corpus) -> None:
    a, b = _ws(), _ws()
    info, chunks = _doc(a, "secret.txt", ["confidential passage"])
    corpus.put_document(a, info, chunks)

    assert corpus.list_documents(b) == []
    assert corpus.search(b, "confidential passage") == []
    assert corpus.find_document(b, info.document_id) is None
