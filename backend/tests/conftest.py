import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def database_url() -> str:
    """A throwaway pgvector database. CI sets DOCQA_REQUIRE_POSTGRES=1 so a missing URL fails, not skips."""
    url = os.environ.get("DOCQA_TEST_DATABASE_URL")
    if url:
        return url
    if os.environ.get("DOCQA_REQUIRE_POSTGRES") == "1":
        pytest.fail("DOCQA_TEST_DATABASE_URL is not set")
    pytest.skip("DOCQA_TEST_DATABASE_URL is not set")


@pytest.fixture(autouse=True)
def _no_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run each test from an empty directory so Settings never reads the developer's .env."""
    monkeypatch.chdir(tmp_path)
