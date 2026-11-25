"""Composition root: the only place that picks adapters and imports vendor SDKs (ADR-0008)."""

from fastapi import FastAPI

from docqa.server import Services, create_app
from docqa.settings import Settings


def build_services(settings: Settings) -> Services:
    return Services(version=settings.docqa_version)


def app_from_env() -> FastAPI:
    """Uvicorn factory: `uvicorn --factory docqa.wiring:app_from_env`."""
    return create_app(build_services(Settings()))
