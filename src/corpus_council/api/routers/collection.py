from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from corpus_council.api.models import (
    CollectionRespondRequest,
    CollectionRespondResponse,
    CollectionStartRequest,
    CollectionStartResponse,
    CollectionStatusResponse,
)
from corpus_council.core.collection import (
    get_collection_status,
    respond_collection,
    start_collection,
)
from corpus_council.core.validation import validate_id

router = APIRouter()


@router.post(
    "/collection/start", response_model=CollectionStartResponse, status_code=201
)
async def post_collection_start(
    request: CollectionStartRequest,
) -> CollectionStartResponse | JSONResponse:
    """POST /collection/start — start a new collection session."""
    from corpus_council.api.app import config, llm, store

    user_id = validate_id(request.user_id, "user_id")
    plan_id = validate_id(request.plan_id, "plan_id")
    session_id = str(uuid.uuid4())
    resolved_mode: str = request.mode or config.deliberation_mode

    try:
        session = start_collection(
            user_id, plan_id, session_id, config, store, llm, mode=resolved_mode
        )
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "plan not found"})

    return CollectionStartResponse(
        user_id=session.user_id,
        session_id=session.session_id,
        first_prompt=session.next_prompt or "",
    )


@router.post("/collection/respond", response_model=CollectionRespondResponse)
async def post_collection_respond(
    request: CollectionRespondRequest,
) -> CollectionRespondResponse | JSONResponse:
    """POST /collection/respond — respond to the current collection prompt."""
    from corpus_council.api.app import config, llm, store

    user_id = validate_id(request.user_id, "user_id")
    session_id = validate_id(request.session_id, "session_id")
    resolved_mode: str = request.mode or config.deliberation_mode

    try:
        session = respond_collection(
            user_id, session_id, request.message, config, store, llm, mode=resolved_mode
        )
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "session not found"})

    return CollectionRespondResponse(
        user_id=session.user_id,
        session_id=session.session_id,
        prompt=session.next_prompt,
        status="complete" if session.status == "complete" else "active",
        collected=session.collected,
    )


@router.get(
    "/collection/{user_id}/{session_id}", response_model=CollectionStatusResponse
)
async def get_collection_status_endpoint(
    user_id: str,
    session_id: str,
) -> CollectionStatusResponse | JSONResponse:
    """GET /collection/{user_id}/{session_id} — get collection session status."""
    from corpus_council.api.app import store

    user_id = validate_id(user_id, "user_id")
    session_id = validate_id(session_id, "session_id")

    try:
        data = get_collection_status(user_id, session_id, store)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "session not found"})

    return CollectionStatusResponse(
        user_id=str(data.get("user_id", user_id)),
        session_id=str(data.get("session_id", session_id)),
        status=str(data.get("status", "active")),
        collected=data.get("collected", {}),
        created_at=str(data.get("created_at", "")),
    )


__all__ = ["router"]
