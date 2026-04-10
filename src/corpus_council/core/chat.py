from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .config import AppConfig
from .consolidated import run_consolidated_deliberation
from .council import load_council_for_goal
from .deliberation import run_deliberation
from .goals import load_goal
from .llm import LLMClient
from .retrieval import ChunkResult, retrieve_chunks
from .store import FileStore


def run_goal_chat(
    goal_name: str,
    user_id: str,
    conversation_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
    mode: str = "sequential",
) -> tuple[str, str]:
    """Load goal, retrieve corpus chunks, run deliberation, persist turn, and return.

    Returns:
        A tuple of (response_text, conversation_id).

    Raises:
        KeyError: if the goal is not found in the manifest.
    """
    # 1. Load goal config — re-raise ValueError as KeyError for 404 mapping
    try:
        goal_config = load_goal(goal_name, config.goals_manifest_path)
    except ValueError as exc:
        raise KeyError(f"Goal not found: {goal_name!r}") from exc

    # 2. Load council members for this goal
    members = load_council_for_goal(goal_config, config.personas_dir)

    # 3. Retrieve corpus chunks — failure is non-fatal
    chunks: list[ChunkResult] = []
    try:
        chunks = retrieve_chunks(message, config)
    except Exception:  # noqa: BLE001
        chunks = []

    # 4. Read existing context — initialize if empty
    context: dict[str, Any] = store.read_json(
        store.goal_context_path(user_id, goal_name, conversation_id)
    )
    if not context:
        context = {
            "user_id": user_id,
            "goal": goal_name,
            "conversation_id": conversation_id,
            "turn_count": 0,
            "last_updated": "",
        }

    # 5. Run deliberation
    if mode == "consolidated":
        result = run_consolidated_deliberation(message, chunks, members, llm)
    else:
        result = run_deliberation(message, chunks, members, llm)

    # 6. Increment turn count
    turn_count: int = int(context.get("turn_count", 0)) + 1

    # 7. Build turn record
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

    # 8. Persist turn to messages.jsonl
    store.append_jsonl(
        store.goal_messages_path(user_id, goal_name, conversation_id), turn_record
    )

    # 9. Persist updated context
    updated_context: dict[str, Any] = {
        "user_id": user_id,
        "goal": goal_name,
        "conversation_id": conversation_id,
        "turn_count": turn_count,
        "last_updated": datetime.now(UTC).isoformat(),
    }
    store.write_json(
        store.goal_context_path(user_id, goal_name, conversation_id), updated_context
    )

    # 10. Return response and conversation_id
    return (result.final_response, conversation_id)


__all__ = ["run_goal_chat"]
