"""Configuration. The only module that reads environment variables (ADR-0008)."""

from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Effort = Literal["low", "medium", "high", "max"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    # Secrets and endpoints
    anthropic_api_key: SecretStr | None = None
    voyage_api_key: SecretStr | None = None
    database_url: SecretStr | None = None
    aws_access_key_id: SecretStr | None = None
    aws_secret_access_key: SecretStr | None = None
    aws_region: str | None = None
    s3_bucket: str | None = None

    # Tracing (LangSmith). wiring.configure_tracing hands these to the langsmith client.
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "docqa-v2"

    # Models
    docqa_writer_model: str = "claude-sonnet-5-5"
    docqa_writer_effort: Effort = "medium"
    docqa_writer_max_tokens: int = 4096
    docqa_small_model: str = "claude-haiku-5-5"
    docqa_small_effort: Effort = "low"
    docqa_embedding_model: str = "voyage-4-lite"
    docqa_embedding_dim: Literal[256, 512, 1024, 2048] = 512  # what Voyage can output
    docqa_judge_model: str = "claude-sonnet-5-5"
    docqa_judge_effort: Effort = "low"

    # Retrieval and limits
    docqa_top_k: int = 4
    docqa_max_rewrites: int = 1
    docqa_daily_question_cap: int = 100

    # Server
    docqa_sample_workspace: str | None = None
    docqa_admin_key: SecretStr | None = None
    docqa_cors_origins: list[str] = []
    docqa_adapters: Literal["live", "memory"] = "live"
    docqa_version: str = "dev"

    @model_validator(mode="after")
    def _live_needs_secrets(self) -> Self:
        if self.docqa_adapters == "live":
            missing = [
                name
                for name in ("anthropic_api_key", "voyage_api_key", "database_url")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError(
                    f"DOCQA_ADAPTERS=live needs {', '.join(n.upper() for n in missing)}"
                )
        return self
