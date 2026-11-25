# ADR-0006: Citations are numbered markers checked in code

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

In v1, refusal lived only in a prompt rule, so it depended on the model obeying.

## Decision

The writer puts `[n]` markers after claims. Code rejects `NO_ANSWER`, drafts without markers, and any marker outside 1..m; every rejection routes to a refusal. The refusal is v1's fixed sentence, word for word, with `refused: true`. Snippets are the first 200 characters of the cited passage, for display only; faithfulness evals judge against the full passage.

## Consequences

Refusal is deterministic. Some answers will be refused falsely; the eval set measures how many.
