"""The Library facade: turning uploaded files into documents (ADR-0012).

Write order on add: validate, then the original to the BlobStore, then the corpus
in one transaction. On remove: the corpus first, then the original. Either way,
a failure at any step leaves the previous version searchable.
"""

import hashlib
import unicodedata
from datetime import UTC, datetime

from docqa.corpus import Corpus
from docqa.domain import DocumentId, DocumentInfo, Upload, WorkspaceId
from docqa.library.blobs import BlobStore
from docqa.library.errors import FileTooLarge, NoTextFound, WorkspaceFull
from docqa.library.loading import classify, load
from docqa.library.splitting import split


def document_id(ws: WorkspaceId, name: str) -> DocumentId:
    """sha256(workspace_id + "/" + file_name)[:16]: same name, same document.
    The name must already be NFC-normalized (see Library.add)."""
    return DocumentId(hashlib.sha256(f"{ws}/{name}".encode()).hexdigest()[:16])


class Library:
    def __init__(
        self,
        corpus: Corpus,
        blobs: BlobStore,
        *,
        max_bytes: int = 10_000_000,
        max_documents: int = 20,
    ) -> None:
        self._corpus = corpus
        self._blobs = blobs
        self._max_bytes = max_bytes
        self._max_documents = max_documents

    def add(self, ws: WorkspaceId, upload: Upload) -> DocumentInfo:
        """Add or replace the document named upload.name. Raises FileTooLarge,
        UnsupportedFileType, WorkspaceFull or NoTextFound."""
        if len(upload.data) > self._max_bytes:
            raise FileTooLarge(f"files are limited to {self._max_bytes} bytes")
        kind = classify(upload.data)
        # macOS sends NFD names, Windows NFC: one visible name must be one document.
        name = unicodedata.normalize("NFC", upload.name)
        doc = document_id(ws, name)
        content_hash = hashlib.sha256(upload.data).hexdigest()

        existing = self._corpus.find_document(ws, doc)
        if existing is not None and existing.content_hash == content_hash:
            return existing
        if existing is None and len(self._corpus.list_documents(ws)) >= self._max_documents:
            raise WorkspaceFull(f"a workspace holds at most {self._max_documents} documents")

        loaded = load(upload.data, kind)
        chunks = split(loaded.pages)
        if not chunks:
            raise NoTextFound("no text could be extracted from the file")

        info = DocumentInfo(
            document_id=doc,
            name=name,
            pages=loaded.page_count,
            chunks=len(chunks),
            content_hash=content_hash,
            uploaded_at=datetime.now(UTC),
        )
        self._blobs.put(ws, doc, name, upload.data, upload.content_type)
        self._corpus.put_document(ws, info, chunks)
        return info

    def list(self, ws: WorkspaceId) -> list[DocumentInfo]:
        return self._corpus.list_documents(ws)

    def remove(self, ws: WorkspaceId, doc: DocumentId) -> None:
        """Remove a document's row, chunks and original. A missing document is a no-op."""
        info = self._corpus.find_document(ws, doc)
        if info is None:
            return
        self._corpus.delete_document(ws, doc)
        self._blobs.delete(ws, doc, info.name)
