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


async def test_post_conversation_returns_200(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/conversation", json={"user_id": "user0001", "message": "Hello"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "user_id" in body
    assert body["user_id"] == "user0001"


async def test_post_conversation_rejects_extra_fields(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/conversation",
        json={"user_id": "user0001", "message": "hi", "foo": "bar"},
    )
    assert response.status_code == 422


async def test_post_collection_start_returns_201(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/collection/start", json={"user_id": "user0001", "plan_id": "signup"}
    )
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body
    assert "first_prompt" in body


async def test_post_collection_start_returns_404_for_missing_plan(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/collection/start",
        json={"user_id": "user0001", "plan_id": "nonexistent"},
    )
    assert response.status_code == 404
    body = response.json()
    assert "error" in body


async def test_post_collection_respond_returns_200(client: httpx.AsyncClient) -> None:
    start = await client.post(
        "/collection/start", json={"user_id": "user0001", "plan_id": "signup"}
    )
    assert start.status_code == 201
    session_id = start.json()["session_id"]

    response = await client.post(
        "/collection/respond",
        json={
            "user_id": "user0001",
            "session_id": session_id,
            "message": "Alice",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "prompt" in body
    assert "collected" in body


async def test_post_collection_respond_returns_404_for_missing_session(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/collection/respond",
        json={
            "user_id": "user0001",
            "session_id": "fake-session-id",
            "message": "hello",
        },
    )
    assert response.status_code == 404


async def test_get_collection_status_returns_200(client: httpx.AsyncClient) -> None:
    start = await client.post(
        "/collection/start", json={"user_id": "user0001", "plan_id": "signup"}
    )
    assert start.status_code == 201
    session_id = start.json()["session_id"]

    response = await client.get(f"/collection/user0001/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert "user_id" in body
    assert "session_id" in body
    assert "status" in body
    assert "collected" in body
    assert "created_at" in body


async def test_get_collection_status_returns_404_for_missing_session(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/collection/user0001/fake-session-id")
    assert response.status_code == 404


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


async def test_post_conversation_invalid_user_id_returns_422(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/conversation", json={"user_id": "ab", "message": "hello"}
    )
    assert response.status_code == 422


async def test_post_conversation_mode_invalid_returns_422(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/conversation",
        json={"user_id": "testuser", "message": "hi", "mode": "invalid_mode"},
    )
    assert response.status_code == 422


async def test_post_conversation_mode_consolidated_returns_200(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/conversation",
        json={"user_id": "testuser", "message": "hi", "mode": "consolidated"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
