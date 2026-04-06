from __future__ import annotations

from fastapi import APIRouter

from corpus_council.api.models import ConversationRequest, ConversationResponse
from corpus_council.core.conversation import run_conversation
from corpus_council.core.validation import validate_id

router = APIRouter()


@router.post("/conversation", response_model=ConversationResponse)
async def post_conversation(request: ConversationRequest) -> ConversationResponse:
    """POST /conversation — run council deliberation and return response."""
    from corpus_council.api.app import config, llm, store

    user_id = validate_id(request.user_id, "user_id")
    resolved_mode: str = request.mode or config.deliberation_mode
    result = run_conversation(
        user_id, request.message, config, store, llm, mode=resolved_mode
    )
    return ConversationResponse(response=result.response, user_id=user_id)


__all__ = ["router"]
