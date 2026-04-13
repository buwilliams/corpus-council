from __future__ import annotations

from typing import Any

import pytest

from corpus_council.core.chat import run_goal_chat
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class ChatTestLLM(LLMClient):
    __test__ = False  # prevent pytest from collecting as test suite

    def call(  # type: ignore[override]
        self,
        template_name: str,
        context: dict[str, Any],
        system_prompt: str | None = None,
    ) -> str:
        self.render_template(template_name, context)  # real template rendering
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        member_name = context.get("member_name", template_name)
        return f"Response from {member_name}"


def _run_one_turn(
    user_id: str,
    goal_name: str,
    conversation_id: str,
    config: AppConfig,
    store: FileStore,
    message: str = "Hello, world!",
) -> tuple[str, str]:
    llm = ChatTestLLM(config)
    return run_goal_chat(
        goal_name=goal_name,
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
        config=config,
        store=store,
        llm=llm,
    )


def test_run_goal_chat_returns_response_and_conversation_id(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """Normal first call returns a non-empty response string and the conversation_id."""
    user_id = "chattest01"
    goal_name = "test-goal"
    conversation_id = "conv-abc-001"

    response, returned_id = _run_one_turn(
        user_id, goal_name, conversation_id, test_config, file_store
    )

    assert isinstance(response, str)
    assert response != ""
    assert returned_id == conversation_id


def test_run_goal_chat_creates_messages_jsonl(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """After a call, messages.jsonl must exist with one record."""
    user_id = "chattest02"
    goal_name = "test-goal"
    conversation_id = "conv-abc-002"

    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)

    messages_path = file_store.goal_messages_path(user_id, goal_name, conversation_id)
    assert messages_path.exists()
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 1


def test_run_goal_chat_messages_jsonl_has_required_fields(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """Turn record must include required keys with non-empty values."""
    user_id = "chattest03"
    goal_name = "test-goal"
    conversation_id = "conv-abc-003"

    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)

    messages_path = file_store.goal_messages_path(user_id, goal_name, conversation_id)
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 1

    record = records[0]
    for key in ("timestamp", "user_message", "deliberation_log", "final_response"):
        assert key in record, f"Missing key: {key!r}"
    assert record["user_message"] == "Hello, world!"
    assert isinstance(record["final_response"], str)
    assert record["final_response"] != ""


def test_run_goal_chat_continuation_turn_count_increments(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """On a second call with the same conversation_id, turn_count increments to 2."""
    user_id = "chattest04"
    goal_name = "test-goal"
    conversation_id = "conv-abc-004"

    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)
    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)

    context_path = file_store.goal_context_path(user_id, goal_name, conversation_id)
    context = file_store.read_json(context_path)
    assert context["turn_count"] == 2


def test_run_goal_chat_continuation_messages_jsonl_grows(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """After two calls with same conversation_id, messages.jsonl has 2 records."""
    user_id = "chattest05"
    goal_name = "test-goal"
    conversation_id = "conv-abc-005"

    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)
    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)

    messages_path = file_store.goal_messages_path(user_id, goal_name, conversation_id)
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 2


def test_run_goal_chat_unknown_goal_raises_key_error(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """An unknown goal name must raise KeyError so the router can map it to 404."""
    user_id = "chattest06"
    conversation_id = "conv-abc-006"
    llm = ChatTestLLM(test_config)

    with pytest.raises(KeyError):
        run_goal_chat(
            goal_name="nonexistent-goal",
            user_id=user_id,
            conversation_id=conversation_id,
            message="Hello?",
            config=test_config,
            store=file_store,
            llm=llm,
        )


def test_run_goal_chat_context_json_created(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    """After first call, context.json must exist with correct fields."""
    user_id = "chattest07"
    goal_name = "test-goal"
    conversation_id = "conv-abc-007"

    _run_one_turn(user_id, goal_name, conversation_id, test_config, file_store)

    context_path = file_store.goal_context_path(user_id, goal_name, conversation_id)
    assert context_path.exists()
    context = file_store.read_json(context_path)
    assert context["turn_count"] == 1
    assert context["user_id"] == user_id
    assert context["goal"] == goal_name
    assert context["conversation_id"] == conversation_id
