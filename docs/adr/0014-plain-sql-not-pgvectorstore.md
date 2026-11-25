# ADR-0014: Plain SQL behind ChunkStore, not langchain-postgres PGVectorStore

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

`PGVectorStore` manages its own tables and connection. That prevents replacing a document's row and chunks in one transaction and makes hybrid search harder.

## Decision

The Postgres adapter uses psycopg 3 and the `pgvector` package directly behind the `ChunkStore` port. LangChain still provides embeddings, splitters, the graph and the checkpointer.

## Consequences

Less use of LangChain's vector-store abstraction. Atomic re-uploads and hybrid search stay within reach.
