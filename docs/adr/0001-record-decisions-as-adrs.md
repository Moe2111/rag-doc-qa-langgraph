# ADR-0001: Record hard-to-reverse decisions as ADRs

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Every agent session starts with no memory of earlier sessions. Decisions made in chat get lost or re-litigated.

## Decision

Record each hard-to-reverse decision as a short ADR in `docs/adr/`. A new ADR supersedes an old one; old ADRs are never edited except to mark them superseded.

## Consequences

A few minutes per decision. Agents read `docs/adr/` before changing anything an ADR covers.
