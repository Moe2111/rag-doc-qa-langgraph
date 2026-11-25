# ADR-0004: Embed with voyage-4-lite at 512 dimensions

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Voyage lists v1's `voyage-3-lite` as legacy. v2 uses a new store, so re-embedding is required anyway.

## Decision

`VoyageAIEmbeddings(model="voyage-4-lite", output_dimension=512)`. The `chunks.embedding` column is `vector(512)`.

## Consequences

The corpus must be re-embedded; v1 and v2 vectors are never mixed. Changing the model or dimension means a schema change and a re-index.
