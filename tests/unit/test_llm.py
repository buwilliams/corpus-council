from __future__ import annotations

import os
from pathlib import Path

import pytest

from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient


def _make_config() -> AppConfig:
    """Build a minimal AppConfig (templates path is hardcoded in LLMClient)."""
    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-20241022",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=Path("/tmp/test/data"),
        corpus_dir=Path("/tmp/test/corpus"),
        council_dir=Path("/tmp/test/council"),
        plans_dir=Path("/tmp/test/plans"),
        chunk_max_size=512,
        retrieval_top_k=3,
        chroma_collection="test_corpus",
    )


def test_render_template_substitutes_variables() -> None:
    """Rendering member_system.md substitutes the member_name variable."""
    client = LLMClient(_make_config())
    result = client.render_template(
        "member_system",
        {
            "member_name": "Alice",
            "persona": "A thoughtful analyst",
            "primary_lens": "accuracy",
            "role_type": "analyst",
            "goal_name": "test-goal",
            "goal_description": "Help the user with their question",
        },
    )
    assert "Alice" in result


def test_render_template_raises_for_missing_template() -> None:
    """Requesting a non-existent template raises FileNotFoundError."""
    client = LLMClient(_make_config())
    with pytest.raises(FileNotFoundError):
        client.render_template("nonexistent_template", {})


def test_render_template_does_not_raise_for_extra_variables() -> None:
    """Extra context variables not referenced in the template do not raise."""
    client = LLMClient(_make_config())
    # member_system.md has known required variables; pass those plus an unused extra
    result = client.render_template(
        "member_system",
        {
            "member_name": "Bob",
            "persona": "A critic",
            "primary_lens": "scrutiny",
            "role_type": "critic",
            "goal_name": "test-goal",
            "goal_description": "Test",
            "extra_var": "this should be silently ignored",
        },
    )
    assert "Bob" in result


@pytest.mark.llm
def test_llm_call_is_skipped_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — skipping real LLM call")

    # Key is set: verify that removing it causes RuntimeError (no real API call made)
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    client = LLMClient(_make_config())
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        client.call(
            "member_deliberation",
            {
                "conversation_history": "",
                "corpus_chunks": "No context.",
                "user_message": "Hello.",
            },
        )
