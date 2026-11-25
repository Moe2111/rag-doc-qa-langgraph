# ADR-0011: Synchronous request handling in phase 1

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

No streaming this sprint, and demo traffic is tiny.

## Decision

Sync FastAPI handlers run in the threadpool; the graph is invoked synchronously.

## Consequences

Simpler code and tests. Move to async when streaming lands.
