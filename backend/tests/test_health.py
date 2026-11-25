import anyio
import httpx

from docqa.settings import Settings
from docqa.wiring import build_services, create_app


def get(path: str, settings: Settings) -> httpx.Response:
    app = create_app(build_services(settings))

    async def call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return anyio.run(call)


def test_health_reports_ok_and_version() -> None:
    settings = Settings.model_validate({"docqa_adapters": "memory", "docqa_version": "abc123"})

    response = get("/health", settings)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "abc123"}
