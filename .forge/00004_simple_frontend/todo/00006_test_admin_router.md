# Task 00006 — Write integration tests for the admin router

## Agent
tester

## Goal
Create `tests/integration/test_admin_router.py` with full integration test coverage for
`src/corpus_council/api/routers/admin.py`. Filesystem operations use real temp directories;
`process_goals` is mocked because it calls the LLM.

## Prerequisites
- Task 00002 (`admin.py`) must be complete
- Task 00003 (routers registered in `app.py`) must be complete

## Context

### Patching strategy for `CONFIG_PATH`
`admin.py` exposes a module-level `CONFIG_PATH: Path = Path("config.yaml")` variable.
Tests patch it via monkeypatch:

```python
import corpus_council.api.routers.admin as admin_module
monkeypatch.setattr(admin_module, "CONFIG_PATH", tmp_path / "config.yaml")
```

### Patching strategy for `process_goals`
`POST /admin/goals/process` calls `process_goals(config.goals_dir, config.personas_dir, config.goals_manifest_path)`.
The test patches `corpus_council.api.routers.admin.process_goals` (the name as imported
inside the route handler).

**Note**: the route handler does `from corpus_council.core.goals import process_goals`
inside the function body. This means the patch target is `corpus_council.core.goals.process_goals`
(the original, since the import happens at call time). Use `unittest.mock.patch` as a
context manager or `monkeypatch.setattr`:

```python
from unittest.mock import MagicMock, patch

with patch("corpus_council.core.goals.process_goals", return_value=[MagicMock(), MagicMock()]) as mock_pg:
    response = await client.post("/admin/goals/process")
    mock_pg.assert_called_once()
```

## Deliverables

Create `tests/integration/test_admin_router.py`:

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import corpus_council.api.app as app_module
import corpus_council.api.routers.admin as admin_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore

MINIMAL_CONFIG_YAML = """\
llm:
  provider: anthropic
  model: claude-haiku-4-5-20251001
embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2
chunking:
  max_size: 512
retrieval:
  top_k: 3
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write a minimal config.yaml and patch CONFIG_PATH to point at it."""
    path = tmp_path / "config.yaml"
    path.write_text(MINIMAL_CONFIG_YAML, encoding="utf-8")
    monkeypatch.setattr(admin_module, "CONFIG_PATH", path)
    return path


@pytest.fixture
async def client(
    config_file: Path,
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


# ---------------------------------------------------------------------------
# Tests: GET /config
# ---------------------------------------------------------------------------

async def test_get_config_returns_200(
    client: httpx.AsyncClient, config_file: Path
) -> None:
    """GET /config returns 200 with content field containing yaml text."""
    response = await client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "llm:" in data["content"]


async def test_get_config_content_matches_disk(
    client: httpx.AsyncClient, config_file: Path
) -> None:
    """GET /config content matches what is on disk verbatim."""
    response = await client.get("/config")
    data = response.json()
    assert data["content"] == config_file.read_text(encoding="utf-8")


async def test_get_config_not_found(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """GET /config returns 404 when config.yaml does not exist."""
    missing = tmp_path / "nonexistent.yaml"
    monkeypatch.setattr(admin_module, "CONFIG_PATH", missing)
    response = await client.get("/config")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: PUT /config
# ---------------------------------------------------------------------------

async def test_put_config_returns_200(
    client: httpx.AsyncClient, config_file: Path
) -> None:
    """PUT /config returns 200 with the new content echoed back."""
    new_content = "# Updated config\n" + MINIMAL_CONFIG_YAML
    response = await client.put("/config", json={"content": new_content})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == new_content


async def test_put_config_writes_to_disk(
    client: httpx.AsyncClient, config_file: Path
) -> None:
    """PUT /config updates the file on disk with the exact supplied content."""
    new_content = "# Modified\n" + MINIMAL_CONFIG_YAML
    await client.put("/config", json={"content": new_content})
    assert config_file.read_text(encoding="utf-8") == new_content


async def test_put_config_preserves_content_verbatim(
    client: httpx.AsyncClient, config_file: Path
) -> None:
    """PUT /config does not re-parse or reformat the YAML (comments preserved)."""
    content_with_comment = "# This comment must survive\n" + MINIMAL_CONFIG_YAML
    await client.put("/config", json={"content": content_with_comment})
    on_disk = config_file.read_text(encoding="utf-8")
    assert "# This comment must survive" in on_disk


# ---------------------------------------------------------------------------
# Tests: POST /admin/goals/process
# ---------------------------------------------------------------------------

async def test_goals_process_returns_200(
    client: httpx.AsyncClient,
) -> None:
    """POST /admin/goals/process returns 200 with goals_processed count."""
    mock_goals = [MagicMock(), MagicMock(), MagicMock()]
    with patch("corpus_council.core.goals.process_goals", return_value=mock_goals):
        response = await client.post("/admin/goals/process")
    assert response.status_code == 200
    data = response.json()
    assert "goals_processed" in data
    assert data["goals_processed"] == 3


async def test_goals_process_zero_goals(
    client: httpx.AsyncClient,
) -> None:
    """POST /admin/goals/process returns 0 when no goals exist."""
    with patch("corpus_council.core.goals.process_goals", return_value=[]):
        response = await client.post("/admin/goals/process")
    assert response.status_code == 200
    assert response.json()["goals_processed"] == 0


# ---------------------------------------------------------------------------
# Tests: Router registration (OpenAPI sanity check)
# ---------------------------------------------------------------------------

async def test_config_and_goals_routes_in_openapi(
    client: httpx.AsyncClient,
) -> None:
    """GET /openapi.json includes /config and /admin/goals/process paths."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/config" in paths
    assert "/admin/goals/process" in paths
```

## Verification

```bash
pytest tests/integration/test_admin_router.py -v
```

All tests must pass. No `pytest.mark.llm` on any test in this file.

## Save Command

```bash
pytest tests/integration/test_admin_router.py -v --tb=short 2>&1 | tail -5
```

Must show all tests passed and exit 0.
