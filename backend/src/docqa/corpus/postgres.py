"""Postgres + pgvector ChunkStore via psycopg 3 (ADR-0013, ADR-0014).

All of the corpus's SQL lives here. Every statement filters on workspace_id so
one workspace can never read another's rows (ADR-0007). A re-upload replaces the
document row and all of its chunks in a single transaction (ADR-0012).
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg import Connection
from psycopg.rows import TupleRow
from psycopg_pool import ConnectionPool

from docqa.domain import Chunk, DocumentId, DocumentInfo, Passage, WorkspaceId

type _Pool = ConnectionPool[Connection[TupleRow]]

_SCHEMA = Path(__file__).parent / "schema.sql"


def _schema_statements() -> list[str]:
    """Split schema.sql into statements. Comment lines are dropped first so a
    semicolon inside a `--` comment never splits a statement."""
    body = "\n".join(
        line for line in _SCHEMA.read_text().splitlines() if not line.lstrip().startswith("--")
    )
    return [s for s in (part.strip() for part in body.split(";")) if s]


class PostgresChunkStore:
    def __init__(self, pool: _Pool) -> None:
        self._pool = pool

    @classmethod
    def connect(cls, url: str) -> "PostgresChunkStore":
        """Apply the schema, then open a pool whose connections speak pgvector."""
        with psycopg.connect(url, autocommit=True) as conn:
            for statement in _schema_statements():
                conn.execute(statement)  # type: ignore[arg-type]  # whole-statement DDL, no params
        pool: _Pool = ConnectionPool(url, min_size=1, configure=register_vector, open=False)
        pool.open()
        return cls(pool)

    def close(self) -> None:
        self._pool.close()

    def put_document(
        self,
        ws: WorkspaceId,
        info: DocumentInfo,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        rows = [
            (ws, info.document_id, c.index, c.page, c.start_index, c.text, Vector(list(vec)))
            for c, vec in zip(chunks, embeddings, strict=True)
        ]
        with self._pool.connection() as conn, conn.transaction():
            conn.execute(
                """
                INSERT INTO documents
                    (workspace_id, document_id, name, pages, chunks, content_hash, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (workspace_id, document_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    pages = EXCLUDED.pages,
                    chunks = EXCLUDED.chunks,
                    content_hash = EXCLUDED.content_hash,
                    uploaded_at = EXCLUDED.uploaded_at
                """,
                (
                    ws,
                    info.document_id,
                    info.name,
                    info.pages,
                    info.chunks,
                    info.content_hash,
                    info.uploaded_at,
                ),
            )
            conn.execute(
                "DELETE FROM chunks WHERE workspace_id = %s AND document_id = %s",
                (ws, info.document_id),
            )
            if rows:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO chunks
                            (workspace_id, document_id, chunk_index, page, start_index, text, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        rows,
                    )

    def list_documents(self, ws: WorkspaceId) -> list[DocumentInfo]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT document_id, name, pages, chunks, content_hash, uploaded_at
                FROM documents WHERE workspace_id = %s
                ORDER BY uploaded_at, document_id
                """,
                (ws,),
            ).fetchall()
        return [_to_info(row) for row in rows]

    def find_document(self, ws: WorkspaceId, doc: DocumentId) -> DocumentInfo | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                SELECT document_id, name, pages, chunks, content_hash, uploaded_at
                FROM documents WHERE workspace_id = %s AND document_id = %s
                """,
                (ws, doc),
            ).fetchone()
        return _to_info(row) if row is not None else None

    def delete_document(self, ws: WorkspaceId, doc: DocumentId) -> None:
        with self._pool.connection() as conn, conn.transaction():
            conn.execute(
                "DELETE FROM documents WHERE workspace_id = %s AND document_id = %s",
                (ws, doc),
            )

    def search(
        self,
        ws: WorkspaceId,
        embedding: Sequence[float],
        *,
        k: int,
        only: Sequence[DocumentId] | None,
    ) -> list[Passage]:
        params: dict[str, Any] = {"q": Vector(list(embedding)), "ws": ws, "k": k}
        sql = """
            SELECT c.document_id, d.name, c.page, c.text, 1 - (c.embedding <=> %(q)s) AS score
            FROM chunks c
            JOIN documents d
              ON d.workspace_id = c.workspace_id AND d.document_id = c.document_id
            WHERE c.workspace_id = %(ws)s
        """
        if only is not None:
            sql += " AND c.document_id = ANY(%(only)s)"
            params["only"] = list(only)
        sql += " ORDER BY c.embedding <=> %(q)s LIMIT %(k)s"
        with self._pool.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            Passage(
                document_id=DocumentId(row[0]), name=row[1], page=row[2], text=row[3], score=row[4]
            )
            for row in rows
        ]


def _to_info(row: tuple[Any, ...]) -> DocumentInfo:
    document_id, name, pages, chunks, content_hash, uploaded_at = row
    return DocumentInfo(
        document_id=DocumentId(document_id),
        name=name,
        pages=pages,
        chunks=chunks,
        content_hash=content_hash,
        uploaded_at=uploaded_at,
    )
