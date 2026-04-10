from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

import corpus_council.api.app as app_module
import corpus_council.api.routers.admin as admin_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(
    tmp_path: Path,
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", LLMClient(test_config))
    monkeypatch.setattr(admin_module, "CONFIG_PATH", tmp_path / "config.yaml")

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tests — GET /config
# ---------------------------------------------------------------------------


async def test_get_config_200(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /config returns 200 and the verbatim file content."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("llm_model: claude-haiku\n", encoding="utf-8")
    monkeypatch.setattr(admin_module, "CONFIG_PATH", config_path)

    response = await client.get("/config")

    assert response.status_code == 200
    assert response.json()["content"] == "llm_model: claude-haiku\n"


async def test_get_config_content_matches_disk(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /config content matches what is on disk byte-for-byte."""
    config_path = tmp_path / "config.yaml"
    expected = "# comment\nkey: value\nanother: 42\n"
    config_path.write_text(expected, encoding="utf-8")
    monkeypatch.setattr(admin_module, "CONFIG_PATH", config_path)

    response = await client.get("/config")

    assert response.status_code == 200
    assert response.json()["content"] == expected


async def test_get_config_404_when_missing(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /config returns 404 when config.yaml does not exist."""
    missing_path = tmp_path / "nonexistent_config.yaml"
    monkeypatch.setattr(admin_module, "CONFIG_PATH", missing_path)

    response = await client.get("/config")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests — PUT /config
# ---------------------------------------------------------------------------


async def test_put_config_200(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUT /config returns 200 with the written content."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(admin_module, "CONFIG_PATH", config_path)

    response = await client.put("/config", json={"content": "llm_model: new-model\n"})

    assert response.status_code == 200
    assert response.json()["content"] == "llm_model: new-model\n"


async def test_put_config_writes_to_disk(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUT /config persists the content to disk."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(admin_module, "CONFIG_PATH", config_path)

    payload = "llm_model: written-model\nembedding_model: all-MiniLM\n"
    await client.put("/config", json={"content": payload})

    assert config_path.read_text(encoding="utf-8") == payload


async def test_put_config_preserves_comments(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUT /config preserves comments and whitespace verbatim."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(admin_module, "CONFIG_PATH", config_path)

    payload = (
        "# This is a top-level comment\n"
        "llm_model: some-model  # inline comment\n"
        "\n"
        "# Another section\n"
        "key: value\n"
    )
    response = await client.put("/config", json={"content": payload})

    assert response.status_code == 200
    assert config_path.read_text(encoding="utf-8") == payload


# ---------------------------------------------------------------------------
# Tests — POST /admin/goals/process
# ---------------------------------------------------------------------------


async def test_post_goals_process_200(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    test_config: AppConfig,
) -> None:
    """POST /admin/goals/process returns 200 with goals_processed count."""
    mock_results = [MagicMock(), MagicMock(), MagicMock()]
    monkeypatch.setattr("corpus_council.core.goals.process_goals", lambda **kw: mock_results)

    response = await client.post("/admin/goals/process")

    assert response.status_code == 200
    assert response.json()["goals_processed"] == 3


async def test_post_goals_process_zero_goals(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    test_config: AppConfig,
) -> None:
    """POST /admin/goals/process returns 0 when there are no goals to process."""
    monkeypatch.setattr("corpus_council.core.goals.process_goals", lambda **kw: [])

    response = await client.post("/admin/goals/process")

    assert response.status_code == 200
    assert response.json()["goals_processed"] == 0


# ---------------------------------------------------------------------------
# Tests — OpenAPI sanity check
# ---------------------------------------------------------------------------


async def test_openapi_contains_config_and_goals_paths(
    client: httpx.AsyncClient,
) -> None:
    """GET /openapi.json includes /config and /admin/goals/process paths."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/config" in paths
    assert "/admin/goals/process" in paths
