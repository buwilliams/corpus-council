from __future__ import annotations

import json

from corpus_council.core.collection import (
    get_collection_status,
    respond_collection,
    start_collection,
)
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class CollTestLLM(LLMClient):
    __test__ = False

    def call(self, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
        self.render_template(template_name, context)  # REAL
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        if template_name == "collection_validate":
            return json.dumps(
                {"valid": True, "extracted_value": "TestValue123", "reason": "ok"}
            )
        if template_name == "collection_prompt":
            return self.render_template(template_name, context)
        return "Response"


def test_collection_completes_when_all_fields_provided(
    test_config: AppConfig, file_store: FileStore
) -> None:
    llm = CollTestLLM(test_config)

    start_collection(
        user_id="user0002",
        plan_id="signup",
        session_id="sess0001",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    # Respond to first field (first_name)
    respond_collection(
        user_id="user0002",
        session_id="sess0001",
        message="Alice",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    # Respond to second field (email)
    result = respond_collection(
        user_id="user0002",
        session_id="sess0001",
        message="alice@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    assert result.status == "complete"
    assert result.next_prompt is None

    collected = file_store.read_json(
        file_store.collection_collected_path("user0002", "sess0001")
    )
    assert "first_name" in collected
    assert "email" in collected


def test_collection_session_persists_across_calls(
    test_config: AppConfig, file_store: FileStore
) -> None:
    llm = CollTestLLM(test_config)

    start_collection(
        user_id="user0002",
        plan_id="signup",
        session_id="sess0002",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    new_store = FileStore(test_config.data_dir)

    result = respond_collection(
        user_id="user0002",
        session_id="sess0002",
        message="Bob",
        config=test_config,
        store=new_store,
        llm=llm,
    )

    # After providing first_name, session should still be active (email still needed)
    assert result.status == "active"


def test_collection_messages_jsonl_has_one_record_per_turn(
    test_config: AppConfig, file_store: FileStore
) -> None:
    llm = CollTestLLM(test_config)

    start_collection(
        user_id="user0002",
        plan_id="signup",
        session_id="sess0003",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0002",
        session_id="sess0003",
        message="Carol",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0002",
        session_id="sess0003",
        message="carol@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    messages = file_store.read_jsonl(
        file_store.collection_messages_path("user0002", "sess0003")
    )
    assert len(messages) == 2


def test_get_collection_status_reflects_completed_session(
    test_config: AppConfig, file_store: FileStore
) -> None:
    llm = CollTestLLM(test_config)

    start_collection(
        user_id="user0002",
        plan_id="signup",
        session_id="sess0004",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0002",
        session_id="sess0004",
        message="Dave",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    respond_collection(
        user_id="user0002",
        session_id="sess0004",
        message="dave@example.com",
        config=test_config,
        store=file_store,
        llm=llm,
    )

    status = get_collection_status(
        user_id="user0002",
        session_id="sess0004",
        store=file_store,
    )

    assert status["status"] == "complete"
    assert "collected" in status
    assert status["collected"]
