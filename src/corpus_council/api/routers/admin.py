from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import (
    ConfigResponse,
    ConfigWriteRequest,
    GoalsListResponse,
    GoalsProcessResponse,
    GoalSummary,
)

router = APIRouter()

CONFIG_PATH: Path = Path("config.yaml")


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """GET /config — read config.yaml verbatim."""
    try:
        content = CONFIG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="config.yaml not found") from exc
    return ConfigResponse(content=content)


@router.put("/config", response_model=ConfigResponse)
async def put_config(request: ConfigWriteRequest) -> ConfigResponse:
    """PUT /config — write config.yaml verbatim (no YAML re-parsing)."""
    try:
        CONFIG_PATH.write_text(request.content, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to write config.yaml: {exc}"
        ) from exc
    return ConfigResponse(content=request.content)


@router.get("/goals", response_model=GoalsListResponse)
async def list_goals() -> GoalsListResponse:
    """GET /goals — return the list of available goals from the manifest."""
    import json

    from corpus_council.api.app import config

    manifest_path = config.goals_manifest_path
    if not manifest_path.exists():
        return GoalsListResponse(goals=[])
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Could not read goals manifest"
        ) from exc
    return GoalsListResponse(
        goals=[GoalSummary(name=g["name"]) for g in data if "name" in g]
    )


@router.post("/admin/goals/process", response_model=GoalsProcessResponse)
async def post_goals_process() -> GoalsProcessResponse:
    """POST /admin/goals/process — process goals and return count."""
    from corpus_council.api.app import config
    from corpus_council.core.goals import process_goals

    try:
        results = process_goals(
            goals_dir=config.goals_dir,
            personas_dir=config.personas_dir,
            manifest_path=config.goals_manifest_path,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GoalsProcessResponse(goals_processed=len(results))


__all__ = ["router"]
