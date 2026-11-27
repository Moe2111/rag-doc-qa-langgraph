"""The BlobStore port: original files at rest. Originals are kept, never served.

Each document has one key, `workspaces/<ws>/<document_id>/<name>`, so a
re-upload overwrites the previous original (ADR-0012).
"""

from typing import Protocol

from docqa.domain import DocumentId, WorkspaceId


def blob_key(ws: WorkspaceId, doc: DocumentId, name: str) -> str:
    return f"workspaces/{ws}/{doc}/{name}"


class BlobStore(Protocol):
    def put(
        self, ws: WorkspaceId, doc: DocumentId, name: str, data: bytes, content_type: str
    ) -> None:
        """Write (or overwrite) the original. Raises if the write fails."""
        ...

    def delete(self, ws: WorkspaceId, doc: DocumentId, name: str) -> None:
        """Delete the original. Deleting a missing original is not an error."""
        ...


class MemoryBlobStore:
    """A dict of key -> (bytes, content type). For tests and DOCQA_ADAPTERS=memory."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put(
        self, ws: WorkspaceId, doc: DocumentId, name: str, data: bytes, content_type: str
    ) -> None:
        self.objects[blob_key(ws, doc, name)] = (data, content_type)

    def delete(self, ws: WorkspaceId, doc: DocumentId, name: str) -> None:
        self.objects.pop(blob_key(ws, doc, name), None)


class S3Client(Protocol):
    """The two boto3 S3 client calls this adapter uses. wiring.py builds the real
    client (ADR-0008); keyword names follow boto3, so they are passed as kwargs."""

    def put_object(self, **kwargs: object) -> object: ...

    def delete_object(self, **kwargs: object) -> object: ...


class S3BlobStore:
    def __init__(self, client: S3Client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put(
        self, ws: WorkspaceId, doc: DocumentId, name: str, data: bytes, content_type: str
    ) -> None:
        self._client.put_object(
            Bucket=self._bucket, Key=blob_key(ws, doc, name), Body=data, ContentType=content_type
        )

    def delete(self, ws: WorkspaceId, doc: DocumentId, name: str) -> None:
        # S3 DeleteObject succeeds on a missing key, matching the port's contract.
        self._client.delete_object(Bucket=self._bucket, Key=blob_key(ws, doc, name))
