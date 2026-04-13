from __future__ import annotations

from pathlib import Path

import pytest

from corpus_council.core.config import AppConfig
from corpus_council.core.council import load_council


def test_load_council_returns_all_members(test_config: AppConfig) -> None:
    members = load_council(test_config)
    assert len(members) == 3


def test_load_council_sorted_by_position_ascending(test_config: AppConfig) -> None:
    members = load_council(test_config)
    positions = [m.position for m in members]
    assert positions == [1, 2, 3]


def test_load_council_parses_all_fields(test_config: AppConfig) -> None:
    members = load_council(test_config)
    for m in members:
        assert m.name
        assert m.persona
        assert m.primary_lens
        assert m.position > 0
        assert m.role_type
        assert m.escalation_rule
        assert m.body
        assert m.source_file


def test_load_council_raises_on_missing_required_field(
    tmp_path: Path, test_config: AppConfig
) -> None:
    bad_dir = tmp_path / "council_bad"
    bad_dir.mkdir()
    (bad_dir / "bad_member.md").write_text(
        "---\n"
        "name: Missing Fields Member\n"
        "persona: A persona\n"
        "primary_lens: lens\n"
        "position: 5\n"
        "role_type: critic\n"
        # escalation_rule is missing
        "---\n"
        "Body text.\n",
        encoding="utf-8",
    )
    bad_config = AppConfig(
        llm_provider=test_config.llm_provider,
        llm_model=test_config.llm_model,
        embedding_provider=test_config.embedding_provider,
        embedding_model=test_config.embedding_model,
        data_dir=test_config.data_dir,
        corpus_dir=test_config.corpus_dir,
        council_dir=bad_dir,


        chunk_max_size=test_config.chunk_max_size,
        retrieval_top_k=test_config.retrieval_top_k,
        chroma_collection=test_config.chroma_collection,
    )
    with pytest.raises(ValueError, match="missing required field"):
        load_council(bad_config)


def test_load_council_raises_on_invalid_position(
    tmp_path: Path, test_config: AppConfig
) -> None:
    bad_dir = tmp_path / "council_invalid_pos"
    bad_dir.mkdir()
    (bad_dir / "invalid_pos.md").write_text(
        "---\n"
        "name: Bad Position Member\n"
        "persona: A persona\n"
        "primary_lens: lens\n"
        "position: not_an_int\n"
        "role_type: critic\n"
        "escalation_rule: Some rule\n"
        "---\n"
        "Body text.\n",
        encoding="utf-8",
    )
    bad_config = AppConfig(
        llm_provider=test_config.llm_provider,
        llm_model=test_config.llm_model,
        embedding_provider=test_config.embedding_provider,
        embedding_model=test_config.embedding_model,
        data_dir=test_config.data_dir,
        corpus_dir=test_config.corpus_dir,
        council_dir=bad_dir,


        chunk_max_size=test_config.chunk_max_size,
        retrieval_top_k=test_config.retrieval_top_k,
        chroma_collection=test_config.chroma_collection,
    )
    with pytest.raises(ValueError, match="position"):
        load_council(bad_config)
