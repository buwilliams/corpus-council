# Task 00007 — Verify conversation and collection router registration

## Agent
tester

## Goal
Create `tests/integration/test_router_registration.py` that confirms all newly registered
routers (`conversation`, `collection`, `files`, `admin`) appear in the OpenAPI schema.
This catches the case where a router is written but not included in `app.py`.

## Prerequisites
- Task 00003 (routers registered in `app.py`) must be complete

## Deliverables

Create `tests/integration/test_router_registration.py`:

```python
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
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", LLMClient(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


async def test_conversation_router_registered(client: httpx.AsyncClient) -> None:
    """POST /conversation is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/conversation" in paths, f"Expected /conversation in paths, got: {list(paths.keys())}"
    assert "post" in paths["/conversation"]


async def test_collection_start_router_registered(client: httpx.AsyncClient) -> None:
    """POST /collection/start is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/collection/start" in paths, (
        f"Expected /collection/start in paths, got: {list(paths.keys())}"
    )
    assert "post" in paths["/collection/start"]


async def test_collection_respond_router_registered(client: httpx.AsyncClient) -> None:
    """POST /collection/respond is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/collection/respond" in paths, (
        f"Expected /collection/respond in paths, got: {list(paths.keys())}"
    )
    assert "post" in paths["/collection/respond"]


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
```

## Verification

```bash
pytest tests/integration/test_router_registration.py -v
```

All six tests must pass.

## Save Command

```bash
pytest tests/integration/test_router_registration.py -v --tb=short 2>&1 | tail -5
```

Must show all tests passed and exit 0.
