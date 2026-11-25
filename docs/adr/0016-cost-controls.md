# ADR-0016: Cost controls for a prepaid Anthropic balance

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Anthropic spend comes from a small prepaid balance. A single abusive client at the per-IP limit could drain it within minutes.

## Decision

Auto-reload stays off, so the balance is a hard ceiling. A global cap of 100 questions per UTC day, stored in Postgres, returns `429 daily_limit_reached`. Per-IP limits stay. Effort settings follow ADR-0005. Evals run in-process (not through the API, so the cap doesn't apply) and are judged by `claude-sonnet-5-5` at effort `low`; the final README numbers may be re-scored with `claude-opus-5-5`.

## Consequences

The demo can stop answering when the cap or the balance runs out, but it can never cause a surprise bill. Raise the cap when the budget allows.
