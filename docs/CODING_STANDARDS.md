# Coding standards

These rules are what code review checks against. CI enforces the first section.

## Enforced by CI

- `ruff format` and `ruff check` (rule set in `backend/pyproject.toml`).
- `pyright` in strict mode over `src/` and `tests/`. No `Any` leaking out of a public function. A `# pyright: ignore[rule]` needs the rule name and a reason on the same line.
- `lint-imports`: layers run `wiring > server > library | answering | quota > corpus > domain`. Sibling feature modules never import each other. Only `wiring` imports `settings`.
- `pytest -W error`: warnings fail the build.

## Modules

- Each module exposes a small interface from its `__init__.py`. Other modules import only that, never a submodule.
- `domain.py` holds shared frozen Pydantic types and nothing else.
- Ports (`ChunkStore`, `BlobStore`, `Models`, `QuotaStore`) are `typing.Protocol`s, each with a real and an in-memory adapter. `wiring.py` is the only place that chooses adapters or constructs vendor clients (ADR-0008).
- All SQL lives in `corpus` and `quota`. Every query filters on `workspace_id` (ADR-0007). SQL uses parameters, never string formatting.
- Use the names in `docs/GLOSSARY.md` in code, API fields, tables and tests.

## Errors

- Domain errors are named exception classes raised by modules (`ThreadNotFound`, `WorkspaceFull`, ...). `server` maps them to HTTP codes; modules never know about HTTP.
- 5xx responses carry a code and a request ID only, never exception text.

## Tests

- Test through public interfaces with in-memory adapters and fakes; don't mock internals.
- One behavior per test, named for the behavior (`test_reupload_replaces_every_old_chunk`).
- Tests never call paid APIs. Anything that needs keys is an eval (`evals/`), not a test.
- Postgres contract tests take the `database_url` fixture and are marked `postgres`. CI runs them against `pgvector/pgvector:0.8.7-pg18`.

## Secrets and logs

- Secrets are `SecretStr` in `Settings` and are read only there. Never log them, and never log question text or document contents.
- Never commit `.env`. Add new variables to `backend/.env.example` and `docs/ARCHITECTURE.md`.

## Changes that need more than review

- Schema, ID scheme or API contract changes (one-way doors): write or supersede an ADR in `docs/adr/` and try to break the change by hand before merging.
- Prompt, model, chunking or `k` changes: attach before/after eval numbers to the PR.
