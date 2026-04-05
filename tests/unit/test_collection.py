from __future__ import annotations

from typing import Any

import pytest

from corpus_council.core.collection import (
    get_collection_status,
    respond_collection,
    start_collection,
)
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class CollectionTestLLM(LLMClient):
    __test__ = False  # prevent pytest from collecting as test suite

    def call(self, template_name: str, context: dict[str, Any]) -> str:
        if template_name == "collection_validate":
            self.render_template(template_name, context)  # validate template renders
            return '{"valid": true, "extracted_value": "TestValue", "reason": "ok"}'
        if template_name == "collection_prompt":
            return self.render_template(template_name, context)
        if template_name == "escalation_check":
            self.render_template(template_name, context)
            return "NOT_TRIGGERED"
        self.render_template(template_name, context)
        return f"Mock response for {template_name}"


def test_start_collection_creates_session_files(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    start_collection(
        user_id="user0001",
        plan_id="signup",
        session_id="sess0001",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    assert file_store.collection_session_path("user0001", "sess0001").exists()
    assert file_store.collection_context_path("user0001", "sess0001").exists()
    assert file_store.collection_collected_path("user0001", "sess0001").exists()


def test_start_collection_returns_first_prompt(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    session = start_collection(
        user_id="user0002",
        plan_id="signup",
        session_id="sess0002",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    assert isinstance(session.next_prompt, str)
    assert session.next_prompt != ""


def test_start_collection_with_invalid_plan_raises(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    with pytest.raises(FileNotFoundError):
        start_collection(
            user_id="user0003",
            plan_id="nonexistent_plan",
            session_id="sess0003",
            config=test_config,
            store=file_store,
            llm=llm,
        )


def test_respond_collection_advances_to_next_field(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    # Start session with 2-field plan (signup has first_name + email)
    start_collection(
        user_id="user0004",
        plan_id="signup",
        session_id="sess0004",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    # Respond to first field
    result = respond_collection(
        user_id="user0004",
        session_id="sess0004",
        message="Alice",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    assert result.status == "active"
    assert result.next_prompt is not None


def test_respond_collection_completes_when_all_fields_collected(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    start_collection(
        user_id="user0005",
        plan_id="signup",
        session_id="sess0005",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    # First field
    respond_collection(
        user_id="user0005",
        session_id="sess0005",
        message="Alice",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    # Second field — should complete
    result = respond_collection(
        user_id="user0005",
        session_id="sess0005",
        message="alice@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    assert result.status == "complete"
    assert result.next_prompt is None


def test_respond_collection_saves_collected_json(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    start_collection(
        user_id="user0006",
        plan_id="signup",
        session_id="sess0006",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0006",
        session_id="sess0006",
        message="Alice",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0006",
        session_id="sess0006",
        message="alice@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    collected_path = file_store.collection_collected_path("user0006", "sess0006")
    collected = file_store.read_json(collected_path)

    assert "first_name" in collected
    assert "email" in collected


def test_respond_collection_appends_to_messages_jsonl(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    start_collection(
        user_id="user0007",
        plan_id="signup",
        session_id="sess0007",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0007",
        session_id="sess0007",
        message="Alice",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0007",
        session_id="sess0007",
        message="alice@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    messages_path = file_store.collection_messages_path("user0007", "sess0007")
    records = file_store.read_jsonl(messages_path)
    assert len(records) == 2


def test_get_collection_status_returns_correct_shape(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    llm = CollectionTestLLM(test_config)
    start_collection(
        user_id="user0008",
        plan_id="signup",
        session_id="sess0008",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    status = get_collection_status(
        user_id="user0008",
        session_id="sess0008",
        store=file_store,
    )

    for key in ("session_id", "user_id", "status", "collected", "created_at"):
        assert key in status, f"Missing key: {key!r}"


def test_get_collection_status_raises_for_missing_session(
    test_config: AppConfig,
    file_store: FileStore,
) -> None:
    with pytest.raises(FileNotFoundError):
        get_collection_status(
            user_id="user0009",
            session_id="nonexistent_session",
            store=file_store,
        )
