# ADR-0015: One idempotent schema.sql applied at startup

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

The schema is small and new; migration tooling would cost time this sprint.

## Decision

`corpus/schema.sql` uses `CREATE ... IF NOT EXISTS` and is applied at startup. `PostgresSaver.setup()` creates its own tables.

## Consequences

No migration history. Adopt Alembic the first time an existing table must change.
