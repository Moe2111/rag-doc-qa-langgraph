# ADR-0012: The documents table is the registry; S3 keeps originals only; corpus owns both tables

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

The document list needs pages, chunk counts and hashes, and a re-upload must never leave stale chunks behind or lose the previous version.

## Decision

A `documents` table holds one row per document. The `corpus` module owns both `documents` and `chunks`, so a re-upload replaces the row and all chunks in one transaction. `Library.add` writes the original to S3 first (same key per document), then commits to Postgres. `Library.remove` deletes from Postgres first, then S3.

## Consequences

If either step fails, the previous version stays searchable. A newer S3 file without a matching database commit is harmless because originals are never served. `library` never touches SQL.
