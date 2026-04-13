from __future__ import annotations

import re

import httpx
import pytest

import corpus_council.api.app as app_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class ChatTestLLM(LLMClient):
    __test__ = False

    def call(  # type: ignore[override]
        self,
        template_name: str,
        context: dict,  # type: ignore[type-arg]
        system_prompt: str | None = None,
    ) -> str:
        self.render_template(template_name, context)  # real rendering
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        if template_name == "council_consolidated":
            return (
                "=== MEMBER: Test Member ===\n"
                "This is a test response.\n"
                "ESCALATION: NONE\n"
                "=== END MEMBER ==="
            )
        return "Mock chat response"


@pytest.fixture
async def client(
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", ChatTestLLM(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


async def test_post_chat_first_message_auto_generates_conversation_id(
    client: httpx.AsyncClient,
) -> None:
    """POST /chat without conversation_id generates a UUID and returns it."""
    response = await client.post(
        "/chat",
        json={"goal": "test-goal", "user_id": "user0001", "message": "hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "goal" in body
    assert "conversation_id" in body
    assert body["goal"] == "test-goal"
    conv_id = body["conversation_id"]
    assert isinstance(conv_id, str)
    assert len(conv_id) > 0
    assert _UUID_RE.match(conv_id), (
        f"Expected UUID-format conversation_id, got: {conv_id!r}"
    )


async def test_post_chat_continuation_uses_same_conversation_id(
    client: httpx.AsyncClient,
    test_config: AppConfig,
) -> None:
    """Second POST with same conversation_id reuses it and persists 2 messages."""
    # First turn — no conversation_id
    first_response = await client.post(
        "/chat",
        json={"goal": "test-goal", "user_id": "user0002", "message": "first message"},
    )
    assert first_response.status_code == 200
    conv_id = first_response.json()["conversation_id"]
    assert isinstance(conv_id, str)

    # Second turn — pass back the conversation_id
    second_response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "user0002",
            "message": "second message",
            "conversation_id": conv_id,
        },
    )
    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conv_id

    # Verify persistence: messages.jsonl must have exactly 2 records
    store = FileStore(test_config.data_dir)
    messages_path = store.goal_messages_path("user0002", "test-goal", conv_id)
    records = store.read_jsonl(messages_path)
    assert len(records) == 2, (
        f"Expected 2 records in messages.jsonl after 2 turns, got {len(records)}"
    )


async def test_post_chat_unknown_goal_returns_404(
    client: httpx.AsyncClient,
) -> None:
    """POST /chat with an unknown goal name returns 404."""
    response = await client.post(
        "/chat",
        json={
            "goal": "nonexistent-goal",
            "user_id": "user0001",
            "message": "hello",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body


async def test_post_chat_invalid_user_id_returns_422(
    client: httpx.AsyncClient,
) -> None:
    """POST /chat with a user_id that is too short returns 422."""
    response = await client.post(
        "/chat",
        json={"goal": "test-goal", "user_id": "x", "message": "hello"},
    )
    assert response.status_code == 422


async def test_post_chat_rejects_extra_fields(
    client: httpx.AsyncClient,
) -> None:
    """POST /chat with extra fields in the request body returns 422."""
    response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "user0001",
            "message": "hi",
            "foo": "bar",
        },
    )
    assert response.status_code == 422


async def test_post_chat_invalid_conversation_id_returns_400(
    client: httpx.AsyncClient,
) -> None:
    """POST /chat with a path-traversal conversation_id returns 400."""
    response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "user0001",
            "message": "hello",
            "conversation_id": "../../../etc",
        },
    )
    assert response.status_code == 400
