from __future__ import annotations

import os
import subprocess
from pathlib import Path

import httpx
import pytest

import corpus_council.api.app as app_module
from corpus_council.core.config import AppConfig
from corpus_council.core.conversation import run_conversation
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


@pytest.mark.llm
async def test_run_conversation_consolidated_mode(
    test_config: AppConfig, file_store: FileStore
) -> None:
    """Real LLM: ingest corpus, embed, then run_conversation in consolidated mode."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    ingest_corpus(test_config)
    embed_corpus(test_config)

    llm = LLMClient(test_config)
    result = run_conversation(
        "testuser",
        "What is artificial intelligence?",
        test_config,
        file_store,
        llm,
        mode="consolidated",
    )

    assert result.response
    assert len(result.response) > 0


@pytest.mark.llm
async def test_post_query_consolidated_via_api(
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real LLM: POST /query with mode=consolidated via httpx, assert 200."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", LLMClient(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/query",
            json={"goal": "test-goal", "message": "Hello", "mode": "consolidated"},
        )

    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert len(body["response"]) > 0


@pytest.mark.llm
def test_query_command_consolidated_mode(
    test_config: AppConfig,
    tmp_path: Path,
) -> None:
    """Real LLM: run corpus-council query via subprocess with --mode consolidated."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    import json

    import yaml

    # Pre-populate corpus so retrieval works in the subprocess
    ingest_corpus(test_config)
    embed_corpus(test_config)

    # Write a goal manifest so the query --goal flag resolves
    goal_manifest_path = tmp_path / "goals_manifest.json"
    goal_manifest_path.write_text(
        json.dumps(
            [
                {
                    "name": "test-goal",
                    "desired_outcome": "Answer AI questions",
                    "corpus_path": str(test_config.corpus_dir),
                    "council": [
                        {"persona_file": "synthesizer.md", "authority_tier": 1},
                        {"persona_file": "analyst.md", "authority_tier": 2},
                        {"persona_file": "critic.md", "authority_tier": 3},
                    ],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": test_config.llm_provider,
            "model": test_config.llm_model,
        },
        "embedding": {
            "provider": test_config.embedding_provider,
            "model": test_config.embedding_model,
        },
        "data_dir": str(test_config.data_dir),
        "corpus_dir": str(test_config.corpus_dir),
        "council_dir": str(test_config.council_dir),
        "templates_dir": str(test_config.templates_dir),
        "plans_dir": str(test_config.plans_dir),
        "chunking": {"max_size": test_config.chunk_max_size},
        "retrieval": {"top_k": test_config.retrieval_top_k},
        "chroma_collection": test_config.chroma_collection,
        "deliberation_mode": test_config.deliberation_mode,
        "personas_dir": str(test_config.personas_dir),
        "goals_manifest_path": str(goal_manifest_path),
    }
    config_path.write_text(yaml.dump(config_data), encoding="utf-8")

    result = subprocess.run(
        [
            "uv",
            "run",
            "corpus-council",
            "query",
            "What is artificial intelligence?",
            "--goal",
            "test-goal",
            "--mode",
            "consolidated",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env={**os.environ},
    )

    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0
