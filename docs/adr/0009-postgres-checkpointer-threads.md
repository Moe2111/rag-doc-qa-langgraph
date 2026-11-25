# ADR-0009: Thread memory in PostgresSaver, scoped to the workspace

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Follow-up questions need history. An in-memory checkpointer would lose threads on every scale-to-zero and pin the app to one replica.

## Decision

Threads are stored by LangGraph's `PostgresSaver` under the key `{workspace_id}/{thread_id}`. A `thread_id` with no checkpoint returns `404 thread_not_found`, and the UI starts a new thread. Only `messages` persists across turns; per-turn state resets on every invoke. Max replicas: 2.

## Consequences

Threads survive restarts and can't be reached from another workspace. LangGraph adds its checkpoint tables to Postgres.
