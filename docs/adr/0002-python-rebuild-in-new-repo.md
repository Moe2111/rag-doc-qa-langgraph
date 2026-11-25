# ADR-0002: Rebuild in Python in a new repo; v1 stays live

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

v1 (`rag-doc-qa`) is a working Next.js app. A separate Azure 8-week rebuild plan also proposed a Python FastAPI backend, which would have meant two parallel backends.

## Decision

Build v2 in a new repo, `Moe2111/rag-doc-qa-langgraph`. v1 stays live and untouched and is the eval baseline (`rag-doc-qa@8db1204`). The Azure 8-week plan is dropped; its Azure work returns as this repo's phase 2 Azure profile (adapters behind the existing ports).

## Consequences

Two codebases; v1's UI is ported, not shared. Only one Python backend to maintain.
