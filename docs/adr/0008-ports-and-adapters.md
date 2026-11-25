# ADR-0008: Ports with real and in-memory adapters

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Tests must run offline with no API keys, and module internals must be replaceable without rewriting tests.

## Decision

`ChunkStore`, `BlobStore`, `Models` and `QuotaStore` are ports with real and in-memory adapters. Embeddings and the checkpointer use LangChain's and LangGraph's own interfaces with fakes. Only `wiring.py` imports vendor SDKs and picks adapters (`DOCQA_ADAPTERS=live|memory`).

## Consequences

Several small interfaces to keep honest; the Postgres contract suite runs against both adapters on every push.
