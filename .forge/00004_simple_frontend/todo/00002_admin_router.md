# Task 00002 — Implement `src/corpus_council/api/routers/admin.py`

## Agent
programmer

## Goal
Create the admin router providing config read/write and a goals-processing trigger endpoint.
This task also adds the required Pydantic models to `models.py`.

## Prerequisites
- Task 00001 must be complete (models.py additions exist)

## Context

### `process_goals` signature (from `src/corpus_council/core/goals.py`)
```python
def process_goals(
    goals_dir: Path, personas_dir: Path, manifest_path: Path
) -> list[GoalConfig]:
```
Returns a list; `len(result)` is the number of goals processed.

### Config path
`app.py` loads config with `load_config(Path("config.yaml"))` — the config file is
`config.yaml` at the working directory. The admin router must use the same path:
`Path("config.yaml")`.

### Existing router pattern
Follows `src/corpus_council/api/routers/query.py` — `from corpus_council.api.app import config`
inside route handlers, not at module level.

## Deliverables

### 1. Add Pydantic models to `src/corpus_council/api/models.py`

Append after the FileWriteRequest model added in task 00001:

```python
class ConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str

class ConfigWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str

class GoalsProcessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals_processed: int
```

### 2. Create `src/corpus_council/api/routers/admin.py`

```python
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import (
    ConfigResponse,
    ConfigWriteRequest,
    GoalsProcessResponse,
)

router = APIRouter()

# The config file is always config.yaml relative to the working directory,
# matching the path used in app.py: load_config(Path("config.yaml")).
# Tests may patch this module-level variable to redirect writes.
CONFIG_PATH: Path = Path("config.yaml")


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """GET /config — return the raw text of config.yaml."""
    path = CONFIG_PATH
    if not path.exists():
        raise HTTPException(status_code=404, detail="config.yaml not found")
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read config") from exc
    return ConfigResponse(content=content)


@router.put("/config", response_model=ConfigResponse)
async def update_config(body: ConfigWriteRequest) -> ConfigResponse:
    """PUT /config — overwrite config.yaml with the supplied text content."""
    path = CONFIG_PATH
    try:
        path.write_text(body.content, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not write config") from exc
    return ConfigResponse(content=body.content)


@router.post("/admin/goals/process", response_model=GoalsProcessResponse)
async def trigger_goals_process() -> GoalsProcessResponse:
    """POST /admin/goals/process — re-process goals and regenerate the manifest."""
    from corpus_council.api.app import config
    from corpus_council.core.goals import process_goals

    goals = process_goals(
        config.goals_dir,
        config.personas_dir,
        config.goals_manifest_path,
    )
    return GoalsProcessResponse(goals_processed=len(goals))


__all__ = ["router"]
```

## Implementation Notes

- `CONFIG_PATH` is a module-level `Path` variable so integration tests can patch it:
  `monkeypatch.setattr("corpus_council.api.routers.admin.CONFIG_PATH", tmp_path / "config.yaml")`.
- `PUT /config` writes the content verbatim — no YAML re-parsing — to preserve comments,
  ordering, and quoting.
- `POST /admin/goals/process` is an LLM-adjacent operation (it validates personas via
  `parse_goal_file`); integration tests should mock `process_goals` at the router level.
- No `path` field exists in `ConfigWriteRequest` — the write destination is always
  `CONFIG_PATH`, never caller-supplied.

## Verification

```bash
ruff check src/
ruff format --check src/
pyright src/
```

All three must exit 0.

## Save Command

```bash
uv run python -c "from corpus_council.api.routers.admin import router; print('import ok')"
```

Must print `import ok` and exit 0.
