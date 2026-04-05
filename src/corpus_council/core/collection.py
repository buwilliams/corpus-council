from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]

from .config import AppConfig
from .llm import LLMClient
from .store import FileStore
from .validation import validate_plan_id


@dataclass
class CollectionSession:
    user_id: str
    session_id: str
    status: str  # "active" | "complete"
    collected: dict[str, Any]
    next_prompt: str | None  # None when complete


def _load_plan(plan_path: Path) -> dict[str, Any]:
    """Parse YAML front matter from a plan file, returning the metadata dict."""
    post = frontmatter.load(str(plan_path))
    return dict(post.metadata)


def start_collection(
    user_id: str,
    plan_id: str,
    session_id: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> CollectionSession:
    """Create a new collection session, generate first question, return state."""
    # 1. Validate and load plan
    plan_path = validate_plan_id(plan_id, config)
    plan_meta = _load_plan(plan_path)

    # 2. Get required fields
    all_fields: list[dict[str, Any]] = [
        f for f in plan_meta.get("fields", []) if f.get("required", False)
    ]
    if not all_fields:
        raise ValueError(f"Plan '{plan_id}' has no required fields")

    first_field = all_fields[0]
    fields_remaining = [str(f["name"]) for f in all_fields]

    now = datetime.now(UTC).isoformat()

    # 3. Initialize session files via store
    store.write_json(
        store.collection_session_path(user_id, session_id),
        {
            "session_id": session_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "created_at": now,
            "completed_at": None,
        },
    )
    store.write_json(
        store.collection_collected_path(user_id, session_id),
        {},
    )
    store.write_json(
        store.collection_context_path(user_id, session_id),
        {
            "session_id": session_id,
            "current_field": str(first_field["name"]),
            "fields_remaining": fields_remaining,
            "last_updated": now,
        },
    )

    # 4. Generate first prompt
    collected_so_far: dict[str, Any] = {}
    prompt = llm.call(
        "collection_prompt",
        {
            "field_name": str(first_field["name"]),
            "field_description": str(first_field.get("description", "")),
            "collected_so_far": json.dumps(collected_so_far),
            "conversation_history": "",
        },
    )

    # 5. Return session state
    return CollectionSession(
        user_id=user_id,
        session_id=session_id,
        status="active",
        collected=collected_so_far,
        next_prompt=prompt,
    )


def respond_collection(
    user_id: str,
    session_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> CollectionSession:
    """Process user response: validate+extract value, advance to next field or complete.

    Appends the turn to messages.jsonl and returns the updated session state.
    """
    # 1. Load session.json — raise FileNotFoundError if missing
    session_data = store.read_json(store.collection_session_path(user_id, session_id))
    if not session_data:
        raise FileNotFoundError(
            f"Session not found: user={user_id!r}, session_id={session_id!r}"
        )

    current_status = str(session_data.get("status", "active"))
    plan_id = str(session_data.get("plan_id", ""))

    # 2. If already complete, return current state immediately
    collected = store.read_json(store.collection_collected_path(user_id, session_id))
    if current_status == "complete":
        return CollectionSession(
            user_id=user_id,
            session_id=session_id,
            status="complete",
            collected=collected,
            next_prompt=None,
        )

    # 3. Load context to get current_field and fields_remaining
    context_data = store.read_json(store.collection_context_path(user_id, session_id))
    current_field = str(context_data.get("current_field", ""))
    fields_remaining: list[str] = list(context_data.get("fields_remaining", []))

    # 4. Load plan to get current field definition
    plan_path = validate_plan_id(plan_id, config)
    plan_meta = _load_plan(plan_path)
    all_fields: list[dict[str, Any]] = list(plan_meta.get("fields", []))

    field_def: dict[str, Any] = {}
    for f in all_fields:
        if str(f.get("name", "")) == current_field:
            field_def = f
            break

    # 5. Validate/extract value using LLM
    validate_response = llm.call(
        "collection_validate",
        {
            "field_name": current_field,
            "field_description": str(field_def.get("description", "")),
            "user_response": message,
            "validation_rule": str(field_def.get("validation_rule", "")),
        },
    )

    # 6. Parse JSON response
    try:
        parsed: dict[str, Any] = json.loads(validate_response)
        is_valid = bool(parsed.get("valid", False))
        extracted_value = str(parsed.get("extracted_value", ""))
    except (json.JSONDecodeError, KeyError):
        is_valid = False
        extracted_value = ""

    now = datetime.now(UTC).isoformat()
    next_prompt: str | None = None
    new_status = "active"

    if is_valid:
        # 7. Update collected.json with new value, remove current field from remaining
        collected[current_field] = extracted_value
        store.write_json(
            store.collection_collected_path(user_id, session_id), collected
        )

        updated_remaining = [f for f in fields_remaining if f != current_field]

        # 8. Check if all fields collected
        if not updated_remaining:
            new_status = "complete"
            next_prompt = None

            # Update session as complete
            session_data["status"] = "complete"
            session_data["completed_at"] = now
            store.write_json(
                store.collection_session_path(user_id, session_id), session_data
            )

            # Update context
            store.write_json(
                store.collection_context_path(user_id, session_id),
                {
                    "session_id": session_id,
                    "current_field": "",
                    "fields_remaining": [],
                    "last_updated": now,
                },
            )
        else:
            # 10. Generate next field prompt
            next_field_name = updated_remaining[0]
            next_field_def: dict[str, Any] = {}
            for f in all_fields:
                if str(f.get("name", "")) == next_field_name:
                    next_field_def = f
                    break

            next_prompt = llm.call(
                "collection_prompt",
                {
                    "field_name": next_field_name,
                    "field_description": str(next_field_def.get("description", "")),
                    "collected_so_far": json.dumps(collected),
                    "conversation_history": "",
                },
            )

            # Update context to next field
            store.write_json(
                store.collection_context_path(user_id, session_id),
                {
                    "session_id": session_id,
                    "current_field": next_field_name,
                    "fields_remaining": updated_remaining,
                    "last_updated": now,
                },
            )
    else:
        # 9. Invalid: regenerate current field prompt (ask again)
        next_prompt = llm.call(
            "collection_prompt",
            {
                "field_name": current_field,
                "field_description": str(field_def.get("description", "")),
                "collected_so_far": json.dumps(collected),
                "conversation_history": "",
            },
        )

        # Update context timestamp
        store.write_json(
            store.collection_context_path(user_id, session_id),
            {
                "session_id": session_id,
                "current_field": current_field,
                "fields_remaining": fields_remaining,
                "last_updated": now,
            },
        )

    # 11. Append turn to messages.jsonl
    turn_record: dict[str, Any] = {
        "timestamp": now,
        "user_message": message,
        "field_name": current_field,
        "valid": is_valid,
        "extracted_value": extracted_value if is_valid else None,
        "next_prompt": next_prompt,
    }
    store.append_jsonl(store.collection_messages_path(user_id, session_id), turn_record)

    # 12. Return CollectionSession
    return CollectionSession(
        user_id=user_id,
        session_id=session_id,
        status=new_status,
        collected=collected,
        next_prompt=next_prompt,
    )


def get_collection_status(
    user_id: str,
    session_id: str,
    store: FileStore,
) -> dict[str, Any]:
    """Return session.json and collected.json merged for API response."""
    session_path = store.collection_session_path(user_id, session_id)
    if not session_path.exists():
        raise FileNotFoundError(
            f"Session not found: user={user_id!r}, session_id={session_id!r}"
        )
    session_data = store.read_json(session_path)
    collected = store.read_json(store.collection_collected_path(user_id, session_id))
    return {**session_data, "collected": collected}


_session_cls = CollectionSession.__name__
__all__ = [
    _session_cls,
    start_collection.__name__,
    respond_collection.__name__,
    get_collection_status.__name__,
]
