# ADR-0013: Postgres + pgvector instead of Pinecone

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

Pinecone would hold vectors only; threads, the document list and the usage counter would each need another store. Pinecone's free plan also caps namespaces at 100.

## Decision

One Postgres with pgvector (HNSW, cosine) holds chunks, documents, threads and the daily usage counter. Hosting: Azure Flexible Server B1MS in Spain Central if the Students subscription gets the 12-month free offer, else Neon's free tier. No paid database tier.

## Consequences

One more service to run. Isolation is a WHERE clause rather than a namespace (see ADR-0007). Contract tests run in CI against a pgvector container with no keys. Hybrid search becomes possible later. The firewall's "allow Azure services" fallback admits any Azure customer's resources; managed identity or private networking is the phase 2 fix.
