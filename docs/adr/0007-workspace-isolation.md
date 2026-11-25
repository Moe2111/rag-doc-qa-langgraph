# ADR-0007: Workspace = browser-made UUID4, enforced by workspace_id in every key and query

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

The demo is public with no accounts, but visitors must not see each other's documents.

## Decision

The browser creates a UUID4 workspace ID. `workspace_id` leads every primary key and every query filters on it. All SQL lives in the `corpus` and `quota` modules. A contract test on every push proves workspace B never sees A's documents, chunks or threads.

## Consequences

A capability link, not authentication: anyone holding the ID can read that workspace, and the README says so. A missing filter would leak data, which is why the contract test exists. Row-level security is phase 2.
