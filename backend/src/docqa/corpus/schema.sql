-- Idempotent corpus schema, applied at startup (ADR-0015). Every table leads
-- with workspace_id so isolation is a primary-key and WHERE-clause fact (ADR-0007).
-- PostgresSaver.setup() owns the checkpoint tables; quota owns daily_usage.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  workspace_id  uuid        NOT NULL,
  document_id   text        NOT NULL,
  name          text        NOT NULL,
  pages         int         NOT NULL,
  chunks        int         NOT NULL,
  content_hash  text        NOT NULL,
  uploaded_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, document_id)
);

CREATE TABLE IF NOT EXISTS chunks (
  workspace_id  uuid        NOT NULL,
  document_id   text        NOT NULL,
  chunk_index   int         NOT NULL,
  page          int,
  start_index   int         NOT NULL,
  text          text        NOT NULL,
  embedding     vector(512) NOT NULL,
  PRIMARY KEY (workspace_id, document_id, chunk_index),
  FOREIGN KEY (workspace_id, document_id) REFERENCES documents ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
