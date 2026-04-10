from __future__ import annotations

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationSummary,
    DeleteConversationResponse,
    MessageRecord,
)
from corpus_council.core.validation import validate_id

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(user_id: str, goal: str) -> ConversationListResponse:
    from corpus_council.api.app import store

    try:
        uid = validate_id(user_id, "user_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    convs = store.list_goal_conversations(uid, goal)
    return ConversationListResponse(
        conversations=[ConversationSummary(conversation_id=c) for c in convs]
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationHistoryResponse
)
async def get_conversation_history(
    conversation_id: str, user_id: str, goal: str
) -> ConversationHistoryResponse:
    from corpus_council.api.app import store

    try:
        uid = validate_id(user_id, "user_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if ".." in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation_id")

    raw = store.read_goal_messages(uid, goal, conversation_id)
    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        goal=goal,
        messages=[
            MessageRecord(
                user=m["user_message"],
                assistant=m["final_response"],
                timestamp=m.get("timestamp"),
            )
            for m in raw
        ],
    )


@router.delete(
    "/conversations/{conversation_id}", response_model=DeleteConversationResponse
)
async def delete_conversation(
    conversation_id: str, user_id: str, goal: str
) -> DeleteConversationResponse:
    from corpus_council.api.app import store

    try:
        uid = validate_id(user_id, "user_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if ".." in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation_id")

    store.delete_goal_conversation(uid, goal, conversation_id)
    return DeleteConversationResponse(status="deleted")


__all__ = ["router"]
