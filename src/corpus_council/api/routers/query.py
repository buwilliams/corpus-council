from __future__ import annotations

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import QueryRequest, QueryResponse
from corpus_council.core.council import load_council_for_goal
from corpus_council.core.goals import load_goal
from corpus_council.core.retrieval import ChunkResult, retrieve_chunks

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def post_query(request: QueryRequest) -> QueryResponse:
    """POST /query — run council deliberation for the given goal and return response."""
    from corpus_council.api.app import config, llm

    # Load goal — raises 404 if not found
    try:
        goal_config = load_goal(request.goal, config.goals_manifest_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=f"Goal {request.goal!r} not found"
        ) from exc

    # Load council members for this goal
    members = load_council_for_goal(goal_config, config.personas_dir)

    # Retrieve corpus chunks — failure is non-fatal
    chunks: list[ChunkResult] = []
    try:
        chunks = retrieve_chunks(request.message, config)
    except Exception:  # noqa: BLE001
        chunks = []

    # Resolve deliberation mode
    resolved_mode: str = request.mode or config.deliberation_mode

    # Run deliberation
    from corpus_council.core.consolidated import run_consolidated_deliberation
    from corpus_council.core.deliberation import run_deliberation

    if resolved_mode == "consolidated":
        result = run_consolidated_deliberation(request.message, chunks, members, llm)
    else:
        result = run_deliberation(request.message, chunks, members, llm)

    return QueryResponse(response=result.final_response, goal=request.goal)


__all__ = ["router"]
