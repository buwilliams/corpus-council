from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

import corpus_council.api.app as app_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class TestLLM(LLMClient):
    __test__ = False

    def call(self, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
        self.render_template(template_name, context)  # real rendering
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        if template_name == "collection_validate":
            return json.dumps(
                {"valid": True, "extracted_value": "TestVal", "reason": "ok"}
            )
        if template_name == "collection_prompt":
            return self.render_template(template_name, context)
        if template_name == "council_consolidated":
            return (
                "=== MEMBER: Test Member ===\n"
                "This is a test response.\n"
                "ESCALATION: NONE\n"
                "=== END MEMBER ==="
            )
        return "Mock response"


@pytest.fixture
async def client(  # type: ignore[override]
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", TestLLM(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


async def test_post_chat_returns_200(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/chat",
        json={"goal": "test-goal", "user_id": "testuser", "message": "What is AI?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "goal" in body
    assert body["goal"] == "test-goal"
    assert "conversation_id" in body


async def test_post_chat_unknown_goal_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/chat",
        json={"goal": "nonexistent-goal", "user_id": "testuser", "message": "hello"},
    )
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body


async def test_post_chat_mode_consolidated_returns_200(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "testuser",
            "message": "hello",
            "mode": "consolidated",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "goal" in body


async def test_post_chat_mode_sequential_returns_200(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "testuser",
            "message": "hello",
            "mode": "sequential",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "goal" in body


async def test_post_chat_rejects_extra_fields(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/chat",
        json={
            "goal": "test-goal",
            "user_id": "testuser",
            "message": "hi",
            "foo": "bar",
        },
    )
    assert response.status_code == 422


async def test_post_corpus_ingest_returns_200(
    client: httpx.AsyncClient, corpus_dir: Path
) -> None:
    response = await client.post("/corpus/ingest", json={"path": str(corpus_dir)})
    assert response.status_code == 200
    body = response.json()
    assert "chunks_created" in body
    assert "files_processed" in body


async def test_post_corpus_embed_returns_200(
    client: httpx.AsyncClient, corpus_dir: Path
) -> None:
    ingest = await client.post("/corpus/ingest", json={"path": str(corpus_dir)})
    assert ingest.status_code == 200

    response = await client.post("/corpus/embed")
    assert response.status_code == 200
    body = response.json()
    assert "vectors_created" in body
