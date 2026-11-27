"""The corpus module: documents and chunks at rest, with vector search.

Public interface (import only these; see docs/ARCHITECTURE.md, Modules):
    Corpus              the facade library/answering use
    ChunkStore          the persistence port
    MemoryChunkStore    the in-memory adapter (tests, DOCQA_ADAPTERS=memory)
    PostgresChunkStore  the Postgres + pgvector adapter

wiring.py is the only caller that picks an adapter (ADR-0008).
"""

from docqa.corpus.memory import MemoryChunkStore
from docqa.corpus.postgres import PostgresChunkStore
from docqa.corpus.service import Corpus
from docqa.corpus.store import ChunkStore

__all__ = ["ChunkStore", "Corpus", "MemoryChunkStore", "PostgresChunkStore"]
