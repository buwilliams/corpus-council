from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .config import AppConfig
from .consolidated import run_consolidated_deliberation
from .council import load_council
from .deliberation import run_deliberation
from .llm import LLMClient
from .retrieval import ChunkResult, retrieve_chunks
from .store import FileStore


@dataclass
class ConversationResult:
    user_id: str
    response: str
    turn_count: int


def run_conversation(
    user_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
    mode: str = "sequential",
) -> ConversationResult:
    """Load context, retrieve chunks, run council deliberation, persist, and return."""
    # 1. Load context, initialise with defaults if empty
    context: dict[str, Any] = store.read_json(store.chat_context_path(user_id))
    if not context:
        context = {
            "user_id": user_id,
            "turn_count": 0,
            "last_updated": "",
            "summary": "",
        }

    # 2. Retrieve corpus chunks — failure is non-fatal (no corpus ingested yet)
    chunks: list[ChunkResult] = []
    try:
        chunks = retrieve_chunks(message, config)
    except Exception:  # noqa: BLE001
        chunks = []

    # 3. Load council
    members = load_council(config)

    # 4. Run deliberation
    if mode == "consolidated":
        result = run_consolidated_deliberation(message, chunks, members, llm)
    else:
        result = run_deliberation(message, chunks, members, llm)

    # 5. Increment turn count
    turn_count: int = int(context.get("turn_count", 0)) + 1

    # 6. Build turn record
    deliberation_log: list[dict[str, Any]] = [
        {
            "member_name": m.member_name,
            "position": m.position,
            "response": m.response,
            "escalation_triggered": m.escalation_triggered,
        }
        for m in result.deliberation_log
    ]
    turn_record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user_message": message,
        "deliberation_log": deliberation_log,
        "final_response": result.final_response,
    }

    # 7. Persist turn to messages.jsonl
    store.append_jsonl(store.chat_messages_path(user_id), turn_record)

    # 8. Persist updated context
    updated_context: dict[str, Any] = {
        "user_id": user_id,
        "turn_count": turn_count,
        "last_updated": datetime.now(UTC).isoformat(),
        "summary": context.get("summary", ""),
    }
    store.write_json(store.chat_context_path(user_id), updated_context)

    # 9. Return result
    return ConversationResult(
        user_id=user_id,
        response=result.final_response,
        turn_count=turn_count,
    )


__all__ = ["ConversationResult", "run_conversation"]
