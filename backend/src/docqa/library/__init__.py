"""The library module: turning uploaded files into documents.

Public interface (import only these; see docs/ARCHITECTURE.md, Modules):
    Library             the facade: add, list, remove
    BlobStore           the originals port
    MemoryBlobStore     the in-memory adapter (tests, DOCQA_ADAPTERS=memory)
    S3BlobStore         the S3 adapter; wiring.py builds its boto3 client
    FileTooLarge, UnsupportedFileType, NoTextFound, WorkspaceFull
                        the domain errors Library.add raises

wiring.py is the only caller that picks an adapter (ADR-0008).
"""

from docqa.library.blobs import BlobStore, MemoryBlobStore, S3BlobStore
from docqa.library.errors import FileTooLarge, NoTextFound, UnsupportedFileType, WorkspaceFull
from docqa.library.service import Library

__all__ = [
    "BlobStore",
    "FileTooLarge",
    "Library",
    "MemoryBlobStore",
    "NoTextFound",
    "S3BlobStore",
    "UnsupportedFileType",
    "WorkspaceFull",
]
