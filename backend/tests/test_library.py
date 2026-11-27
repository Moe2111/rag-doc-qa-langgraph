"""Library starter tests (docs/ARCHITECTURE.md): memory adapters, fake embeddings."""

import unicodedata
from collections.abc import Sequence
from io import BytesIO

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from pypdf import PdfWriter
from pypdf.generic import ContentStream, DictionaryObject, NameObject

from docqa.corpus import Corpus, MemoryChunkStore
from docqa.domain import Chunk, DocumentId, DocumentInfo, Passage, Upload, WorkspaceId
from docqa.library import (
    FileTooLarge,
    Library,
    MemoryBlobStore,
    NoTextFound,
    S3BlobStore,
    UnsupportedFileType,
    WorkspaceFull,
)

WS = WorkspaceId("3f0c1b9e-6a51-4d4e-9a57-0c0d8f6f2a11")
OTHER_WS = WorkspaceId("9b2d7c41-1e0f-4f7a-8b3c-5d6e7f8a9b0c")


class CountingEmbeddings(DeterministicFakeEmbedding):
    embedded_texts: int = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts += len(texts)
        return super().embed_documents(texts)


class FailingBlobStore(MemoryBlobStore):
    """Puts succeed until fail_puts is set."""

    fail_puts = False

    def put(
        self, ws: WorkspaceId, doc: DocumentId, name: str, data: bytes, content_type: str
    ) -> None:
        if self.fail_puts:
            raise ConnectionError("S3 is down")
        super().put(ws, doc, name, data, content_type)


class FailingChunkStore(MemoryChunkStore):
    """put_document succeeds until fail_puts is set; a failure changes nothing."""

    fail_puts = False

    def put_document(
        self,
        ws: WorkspaceId,
        info: DocumentInfo,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if self.fail_puts:
            raise ConnectionError("Postgres is down")
        super().put_document(ws, info, chunks, embeddings)


def _library(
    store: MemoryChunkStore | None = None,
    blobs: MemoryBlobStore | None = None,
    embeddings: CountingEmbeddings | None = None,
) -> tuple[Library, Corpus, MemoryBlobStore]:
    corpus = Corpus(store or MemoryChunkStore(), embeddings or CountingEmbeddings(size=16))
    blobs = blobs if blobs is not None else MemoryBlobStore()
    return Library(corpus, blobs), corpus, blobs


def _text(name: str, body: str) -> Upload:
    return Upload(name=name, content_type="text/plain", data=body.encode())


def _all_passages(corpus: Corpus, ws: WorkspaceId = WS) -> list[Passage]:
    return corpus.search(ws, "anything", k=10_000)


def _pdf(*page_texts: str | None) -> bytes:
    """A PDF with one page per argument; None makes a page with no text layer."""
    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        if text is None:
            continue
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        stream = ContentStream(None, writer)
        stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode())
        page.replace_contents(stream)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


LONG = " ".join(f"Long version sentence {i} about access control." for i in range(300))


def test_add_returns_the_listed_document_info() -> None:
    library, _, _ = _library()

    info = library.add(WS, _text("notes.md", LONG))

    assert (info.name, info.pages) == ("notes.md", 1)
    assert info.chunks > 1
    assert library.list(WS) == [info]


def test_add_makes_every_chunk_searchable() -> None:
    library, corpus, _ = _library()

    info = library.add(WS, _text("notes.md", LONG))

    passages = _all_passages(corpus)
    assert len(passages) == info.chunks
    assert {(p.document_id, p.page) for p in passages} == {(info.document_id, None)}


def test_add_stores_the_original() -> None:
    library, _, blobs = _library()

    info = library.add(WS, _text("notes.md", "hello"))

    assert blobs.objects == {
        f"workspaces/{WS}/{info.document_id}/notes.md": (b"hello", "text/plain")
    }


def test_chunks_break_at_paragraphs_and_collapse_spaces() -> None:
    library, corpus, _ = _library()
    # Together over the 1,500-char chunk size, each under it: one chunk per paragraph.
    first = "First paragraph   with\t extra  spaces. " * 30
    second = "Second paragraph. " * 30

    library.add(WS, _text("notes.md", f"{first}\r\n\r\n\r\n\r\n{second}"))

    texts = sorted(p.text for p in _all_passages(corpus))
    assert texts == sorted([" ".join(first.split()), " ".join(second.split())])


def test_document_id_depends_on_workspace_and_name() -> None:
    library, _, _ = _library()

    a = library.add(WS, _text("a.txt", "alpha"))
    b = library.add(WS, _text("b.txt", "alpha"))
    other = library.add(OTHER_WS, _text("a.txt", "alpha"))

    assert len({a.document_id, b.document_id, other.document_id}) == 3
    assert len(a.document_id) == 16


def test_names_that_differ_only_in_unicode_normalization_are_one_document() -> None:
    library, _, _ = _library()
    nfc = library.add(WS, _text(unicodedata.normalize("NFC", "café.txt"), "first"))

    nfd = library.add(WS, _text(unicodedata.normalize("NFD", "café.txt"), "second"))

    assert nfd.document_id == nfc.document_id
    assert library.list(WS) == [nfd]


def test_reupload_replaces_every_old_chunk_even_when_shorter() -> None:
    library, corpus, blobs = _library()
    first = library.add(WS, _text("policy.txt", LONG))

    second = library.add(WS, _text("policy.txt", "Short version."))

    assert second.document_id == first.document_id
    assert first.chunks > 1
    assert second.chunks == 1
    assert [p.text for p in _all_passages(corpus)] == ["Short version."]
    assert library.list(WS) == [second]
    assert list(blobs.objects.values()) == [(b"Short version.", "text/plain")]


def test_unchanged_reupload_skips_embedding() -> None:
    embeddings = CountingEmbeddings(size=16)
    library, _, _ = _library(embeddings=embeddings)
    first = library.add(WS, _text("policy.txt", LONG))
    embedded = embeddings.embedded_texts

    again = library.add(WS, _text("policy.txt", LONG))

    assert again == first
    assert embeddings.embedded_texts == embedded


def test_file_over_the_limit_is_too_large() -> None:
    library, _, _ = _library()
    data = b"a" * 11_000_000

    with pytest.raises(FileTooLarge):
        library.add(WS, Upload(name="big.txt", content_type="text/plain", data=data))


def test_docx_is_unsupported() -> None:
    library, _, _ = _library()
    docx = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00" + bytes(range(256))

    with pytest.raises(UnsupportedFileType):
        library.add(WS, Upload(name="report.docx", content_type="text/plain", data=docx))


def test_corrupt_pdf_is_unsupported() -> None:
    library, _, _ = _library()

    with pytest.raises(UnsupportedFileType):
        library.add(WS, Upload(name="x.pdf", content_type="application/pdf", data=b"%PDF-1.7\n"))


def test_image_only_pdf_has_no_text() -> None:
    library, corpus, blobs = _library()

    with pytest.raises(NoTextFound):
        library.add(WS, Upload(name="scan.pdf", content_type="application/pdf", data=_pdf(None)))
    assert library.list(WS) == []
    assert _all_passages(corpus) == []
    assert blobs.objects == {}


def test_s3_failure_on_reupload_leaves_previous_version_searchable() -> None:
    blobs = FailingBlobStore()
    library, corpus, _ = _library(blobs=blobs)
    first = library.add(WS, _text("policy.txt", LONG))
    blobs.fail_puts = True

    with pytest.raises(ConnectionError):
        library.add(WS, _text("policy.txt", "Short version."))

    assert library.list(WS) == [first]
    assert len(_all_passages(corpus)) == first.chunks


def test_corpus_failure_after_s3_write_leaves_previous_version_intact() -> None:
    store = FailingChunkStore()
    library, corpus, blobs = _library(store=store)
    first = library.add(WS, _text("policy.txt", LONG))
    store.fail_puts = True

    with pytest.raises(ConnectionError):
        library.add(WS, _text("policy.txt", "Short version."))

    assert library.list(WS) == [first]
    assert len(_all_passages(corpus)) == first.chunks
    # The newer original is left in S3; harmless because originals are never served.
    assert list(blobs.objects.values()) == [(b"Short version.", "text/plain")]


def test_remove_deletes_chunks_row_and_original() -> None:
    library, corpus, blobs = _library()
    kept = library.add(WS, _text("keep.txt", "keep me"))
    gone = library.add(WS, _text("gone.txt", LONG))

    library.remove(WS, gone.document_id)

    assert library.list(WS) == [kept]
    assert {p.document_id for p in _all_passages(corpus)} == {kept.document_id}
    assert len(blobs.objects) == 1


def test_remove_of_unknown_document_is_a_no_op() -> None:
    library, _, _ = _library()

    library.remove(WS, DocumentId("0123456789abcdef"))

    assert library.list(WS) == []


def _fill(library: Library, ws: WorkspaceId = WS) -> None:
    for i in range(20):
        library.add(ws, _text(f"doc-{i}.txt", f"document {i}"))


def test_twenty_first_document_makes_workspace_full() -> None:
    library, _, _ = _library()
    _fill(library)

    with pytest.raises(WorkspaceFull):
        library.add(WS, _text("doc-20.txt", "one too many"))


def test_full_workspace_still_accepts_a_replacement() -> None:
    library, _, _ = _library()
    _fill(library)

    info = library.add(WS, _text("doc-0.txt", "a new version"))

    assert len(library.list(WS)) == 20
    assert info in library.list(WS)


def test_a_full_workspace_does_not_limit_another() -> None:
    library, _, _ = _library()
    _fill(library)

    library.add(OTHER_WS, _text("doc-20.txt", "fine here"))

    assert len(library.list(OTHER_WS)) == 1


def test_pdf_chunks_carry_one_based_page_numbers() -> None:
    library, corpus, _ = _library()

    info = library.add(
        WS, Upload(name="two.pdf", content_type="application/pdf", data=_pdf("One", "Two"))
    )

    assert info.pages == 2
    assert sorted((p.page, p.text) for p in _all_passages(corpus)) == [(1, "One"), (2, "Two")]


def test_blank_pdf_pages_count_but_hold_no_chunks() -> None:
    library, corpus, _ = _library()

    info = library.add(
        WS, Upload(name="gap.pdf", content_type="application/pdf", data=_pdf("One", None, "Three"))
    )

    assert info.pages == 3
    assert {p.page for p in _all_passages(corpus)} == {1, 3}


class RecordingS3Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def put_object(self, **kwargs: object) -> object:
        self.calls.append(("put_object", kwargs))
        return {}

    def delete_object(self, **kwargs: object) -> object:
        self.calls.append(("delete_object", kwargs))
        return {}


def test_s3_blob_store_uses_one_key_per_document() -> None:
    client = RecordingS3Client()
    store = S3BlobStore(client, "bucket")
    doc = DocumentId("0123456789abcdef")

    store.put(WS, doc, "a.pdf", b"%PDF-", "application/pdf")
    store.delete(WS, doc, "a.pdf")

    key = f"workspaces/{WS}/{doc}/a.pdf"
    assert client.calls == [
        (
            "put_object",
            {"Bucket": "bucket", "Key": key, "Body": b"%PDF-", "ContentType": "application/pdf"},
        ),
        ("delete_object", {"Bucket": "bucket", "Key": key}),
    ]
