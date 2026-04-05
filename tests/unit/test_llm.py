from __future__ import annotations

import os
from pathlib import Path

import pytest

from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient


def _make_config(templates_dir: Path) -> AppConfig:
    """Build a minimal AppConfig pointing templates_dir at the given path."""
    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-20241022",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=templates_dir.parent / "data",
        corpus_dir=templates_dir.parent / "corpus",
        council_dir=templates_dir.parent / "council",
        templates_dir=templates_dir,
        plans_dir=templates_dir.parent / "plans",
        chunk_max_size=512,
        retrieval_top_k=3,
        chroma_collection="test_corpus",
    )


def test_render_template_substitutes_variables(tmp_path: Path) -> None:
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    (tpl_dir / "greet.md").write_text(
        "Hello, {{ name }}! Welcome to {{ place }}.",
        encoding="utf-8",
    )
    config = _make_config(tpl_dir)
    client = LLMClient(config)
    result = client.render_template("greet", {"name": "Alice", "place": "Wonderland"})
    assert "Alice" in result
    assert "Wonderland" in result
    assert "Hello, Alice! Welcome to Wonderland." in result


def test_render_template_raises_for_missing_template(tmp_path: Path) -> None:
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    config = _make_config(tpl_dir)
    client = LLMClient(config)
    with pytest.raises(FileNotFoundError):
        client.render_template("nonexistent_template", {})


def test_render_template_does_not_expose_unknown_variables(tmp_path: Path) -> None:
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    (tpl_dir / "simple.md").write_text(
        "Known: {{ known_var }}",
        encoding="utf-8",
    )
    config = _make_config(tpl_dir)
    client = LLMClient(config)
    # extra_var is not in template — should not raise
    result = client.render_template(
        "simple", {"known_var": "hello", "extra_var": "ignored"}
    )
    assert "hello" in result


@pytest.mark.llm
def test_llm_call_is_skipped_without_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — skipping real LLM call")

    # Key is set: verify that removing it causes RuntimeError (no real API call made)
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    (tpl_dir / "ping.md").write_text("Say hello.", encoding="utf-8")
    config = _make_config(tpl_dir)
    client = LLMClient(config)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        client.call("ping", {})
