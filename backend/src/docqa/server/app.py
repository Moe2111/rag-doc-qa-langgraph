from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


@dataclass(frozen=True)
class Services:
    """Everything the HTTP layer needs, built by wiring.build_services."""

    version: str


class Health(BaseModel):
    status: Literal["ok"]
    version: str


def create_app(services: Services) -> FastAPI:
    app = FastAPI(title="DocQA v2", version=services.version)

    @app.get("/health")
    def health() -> Health:  # pyright: ignore[reportUnusedFunction]
        return Health(status="ok", version=services.version)

    return app
