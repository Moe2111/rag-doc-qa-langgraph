"""Composition root: the only place that picks adapters and imports vendor SDKs (ADR-0008)."""

import os

from fastapi import FastAPI
from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import DeterministicFakeEmbedding, Embeddings
from langchain_voyageai import VoyageAIEmbeddings
from pydantic import SecretStr

from docqa.answering import ClaudeModels
from docqa.server import Services, create_app
from docqa.settings import Settings


def _required(secret: SecretStr | None, name: str) -> SecretStr:
    if secret is None:  # Settings already rejects this in live mode
        raise ValueError(f"{name} is not set")
    return secret


def configure_tracing(settings: Settings) -> None:
    """LangSmith reads its config from the process environment, not from Settings.
    Tracing is on only when it is enabled and a key is set."""
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        os.environ["LANGSMITH_TRACING"] = "false"
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


def build_embeddings(settings: Settings) -> Embeddings:
    """Voyage in live mode; a deterministic fake (no network) in memory mode."""
    if settings.docqa_adapters == "memory":
        return DeterministicFakeEmbedding(size=settings.docqa_embedding_dim)
    return VoyageAIEmbeddings(
        model=settings.docqa_embedding_model,
        output_dimension=settings.docqa_embedding_dim,
        api_key=_required(settings.voyage_api_key, "VOYAGE_API_KEY"),
        batch_size=128,
    )


def build_models(settings: Settings) -> ClaudeModels:
    """Sonnet writes; Haiku contextualizes, grades and rewrites (ADR-0005)."""
    writer = ChatAnthropic(
        model_name=settings.docqa_writer_model,
        max_tokens_to_sample=settings.docqa_writer_max_tokens,
        output_config={"effort": settings.docqa_writer_effort},
        api_key=_required(settings.anthropic_api_key, "ANTHROPIC_API_KEY"),
        timeout=None,
        stop=None,
    )
    small = ChatAnthropic(
        model_name=settings.docqa_small_model,
        max_tokens_to_sample=settings.docqa_small_max_tokens,
        output_config={"effort": settings.docqa_small_effort},
        api_key=_required(settings.anthropic_api_key, "ANTHROPIC_API_KEY"),
        timeout=None,
        stop=None,
    )
    return ClaudeModels(writer=writer, small=small)


def build_services(settings: Settings) -> Services:
    return Services(version=settings.docqa_version)


def app_from_env() -> FastAPI:
    """Uvicorn factory: `uvicorn --factory docqa.wiring:app_from_env`."""
    return create_app(build_services(Settings()))
