from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import ChatRequest, ChatResponse
from corpus_council.core.validation import validate_id

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    """POST /chat — stateful, goal-aware chat."""
    from corpus_council.api.app import config, llm, store
    from corpus_council.core.chat import run_goal_chat

    # Validate user_id
    try:
        user_id = validate_id(request.user_id, "user_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Validate conversation_id for path traversal
    if request.conversation_id is not None and ".." in request.conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation_id")

    # Generate conversation_id if not supplied
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Resolve deliberation mode
    resolved_mode: str = request.mode or config.deliberation_mode

    # Run goal chat
    try:
        resp, conv_id = run_goal_chat(
            goal_name=request.goal,
            user_id=user_id,
            conversation_id=conversation_id,
            message=request.message,
            config=config,
            store=store,
            llm=llm,
            mode=resolved_mode,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatResponse(response=resp, goal=request.goal, conversation_id=conv_id)


__all__ = ["router"]
