import pytest
from pydantic import ValidationError

from docqa.settings import Settings


def test_memory_adapters_need_no_secrets() -> None:
    settings = Settings.model_validate({"docqa_adapters": "memory"})

    assert settings.docqa_writer_model == "claude-sonnet-5-5"
    assert settings.docqa_embedding_dim == 512


def test_live_adapters_name_the_missing_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ANTHROPIC_API_KEY", "VOYAGE_API_KEY", "DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY, VOYAGE_API_KEY, DATABASE_URL"):
        Settings.model_validate({"docqa_adapters": "live"})


def test_secrets_are_not_printed() -> None:
    settings = Settings.model_validate(
        {"docqa_adapters": "memory", "anthropic_api_key": "sk-secret"}
    )

    assert "sk-secret" not in repr(settings)
