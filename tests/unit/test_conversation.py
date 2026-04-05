from __future__ import annotations

from typing import Any

from corpus_council.core.config import AppConfig
from corpus_council.core.conversation import ConversationResult, run_conversation
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class ConvTestLLM(LLMClient):
    __test__ = False  # prevent pytest from collecting as test suite

    def call(self, template_name: str, context: dict[str, Any]) -> str:
        self.render_template(template_name, context)  # real template rendering
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        member_name = context.get("member_name", template_name)
        return f"Response from {member_name}"


def _run_one_turn(
    user_id: str,
    config: AppConfig,
    store: FileStore,
) -> ConversationResult:
    llm = ConvTestLLM(config)
    return run_conversation(
        user_id=user_id,
        message="Hello, world!",
        config=config,
        store=store,
        llm=llm,
    )


def test_conversation_run_creates_messages_jsonl(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_id = "testuser01"
    _run_one_turn(user_id, test_config, file_store)

    messages_path = file_store.chat_messages_path(user_id)
    assert messages_path.exists()
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 1


def test_conversation_run_updates_context_json(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_id = "testuser02"
    _run_one_turn(user_id, test_config, file_store)

    context_path = file_store.chat_context_path(user_id)
    assert context_path.exists()
    context = file_store.read_json(context_path)
    assert context["turn_count"] == 1


def test_conversation_resume_loads_prior_context(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_id = "testuser03"

    # First turn
    result1 = _run_one_turn(user_id, test_config, file_store)
    assert result1.turn_count == 1

    # Second turn — same user_id, should resume from existing context
    result2 = _run_one_turn(user_id, test_config, file_store)
    assert result2.turn_count == 2

    messages_path = file_store.chat_messages_path(user_id)
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 2


def test_conversation_messages_jsonl_has_required_fields(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_id = "testuser04"
    _run_one_turn(user_id, test_config, file_store)

    messages_path = file_store.chat_messages_path(user_id)
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 1

    record = records[0]
    for key in ("timestamp", "user_message", "deliberation_log", "final_response"):
        assert key in record, f"Missing key: {key!r}"


def test_conversation_returns_non_empty_response(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_id = "testuser05"
    result = _run_one_turn(user_id, test_config, file_store)
    assert result.response != ""


def test_conversation_different_users_isolated(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    user_a = "useralpha1"
    user_b = "userbeta01"

    _run_one_turn(user_a, test_config, file_store)
    _run_one_turn(user_b, test_config, file_store)

    path_a = file_store.chat_messages_path(user_a)
    path_b = file_store.chat_messages_path(user_b)

    assert path_a != path_b

    records_a = file_store.read_jsonl(path_a)
    records_b = file_store.read_jsonl(path_b)

    assert len(records_a) == 1
    assert len(records_b) == 1
