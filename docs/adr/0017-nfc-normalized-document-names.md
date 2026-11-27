# ADR-0017: Document names are NFC-normalized before the document ID is hashed

- Status: accepted
- Date: 2026-11-27
- Details: docs/ARCHITECTURE.md (IDs)

## Context

`document_id` is `sha256(workspace_id + "/" + file_name)[:16]`, so the same name in a workspace is the same document and a re-upload replaces it. Unicode allows one visible name to have two byte forms: macOS file pickers send decomposed names (NFD, `e` + combining accent), Windows sends composed ones (NFC, `é`). Hashed as-is, `café.pdf` from each would be two documents with the same visible name, and a re-upload from the other OS would add a duplicate instead of replacing it. Found by hand when trying to break the ID scheme in T3.

## Decision

`Library.add` normalizes the uploaded name to NFC once, then uses that form for the document ID, the stored `documents.name` and the S3 key. Nothing had been stored under the un-normalized scheme, so no migration is needed.

## Consequences

One visible name is one document on every OS. Names that differ only in other ways (case, surrounding spaces, compatibility forms such as full-width letters) are still different documents; name validation belongs to the server (T5). Changing the normalization later would change existing IDs, so it needs a superseding ADR and a re-key.
