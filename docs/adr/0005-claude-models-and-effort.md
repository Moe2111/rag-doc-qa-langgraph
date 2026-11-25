# ADR-0005: Sonnet 5.5 writes; Haiku 5.5 handles the small roles

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

v1 used Claude. Keeping the vendor means the v1/v2 comparison measures the framework and design, not the model vendor. Spend comes from a small prepaid balance.

## Decision

`claude-sonnet-5-5` at effort `medium` with `max_tokens` 4096 writes answers. `claude-haiku-5-5` at effort `low` contextualizes, grades and rewrites. Model names and effort levels are configuration. An API `stop_reason` of `refusal` is treated as `NO_ANSWER`.

## Consequences

Routing calls are cheap. Effort levels are tuned from eval numbers, not guesses. An Azure OpenAI profile stays possible because model names are config.
