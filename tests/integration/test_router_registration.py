from __future__ import annotations

import httpx
import pytest

import corpus_council.api.app as app_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


@pytest.fixture
async def client(
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.users_dir))
    monkeypatch.setattr(app_module, "llm", LLMClient(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


async def test_chat_router_registered(client: httpx.AsyncClient) -> None:
    """POST /chat is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/chat" in paths, f"Expected /chat in paths, got: {list(paths.keys())}"
    assert "post" in paths["/chat"]


async def test_files_router_registered(client: httpx.AsyncClient) -> None:
    """GET /files is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/files" in paths, f"Expected /files in paths, got: {list(paths.keys())}"
    assert "get" in paths["/files"]


async def test_admin_config_router_registered(client: httpx.AsyncClient) -> None:
    """GET /config is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/config" in paths, f"Expected /config in paths, got: {list(paths.keys())}"


async def test_admin_goals_process_router_registered(client: httpx.AsyncClient) -> None:
    """POST /admin/goals/process is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/admin/goals/process" in paths, (
        f"Expected /admin/goals/process in paths, got: {list(paths.keys())}"
    )
    assert "post" in paths["/admin/goals/process"]
