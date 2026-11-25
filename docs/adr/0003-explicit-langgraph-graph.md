# ADR-0003: Answering is an explicit LangGraph graph, not a free agent

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

The product's promise is refusal: no answer without a valid citation. A tool-calling agent chooses its own path, which makes that hard to guarantee and cost hard to bound.

## Decision

A fixed `StateGraph`: contextualize, retrieve, grade, at most one rewrite, write, check, refuse. The only path to an answer runs through the code-level citation check.

## Consequences

Refusal is testable offline with scripted models. Cost is bounded at 2 searches and 5 Claude calls per question. Multi-hop questions are out of reach; an agent mode can come in phase 2 behind `Answerer.ask`.
