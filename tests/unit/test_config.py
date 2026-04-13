from __future__ import annotations

from pathlib import Path

import pytest

from corpus_council.core.config import AppConfig, load_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REAL_CONFIG = Path(__file__).parent.parent.parent / "config.yaml"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_config_returns_all_required_fields() -> None:
    """Load the real config.yaml and assert every AppConfig field is populated."""
    config = load_config(_REAL_CONFIG)

    assert isinstance(config, AppConfig)
    assert config.llm_provider
    assert config.llm_model
    assert config.embedding_provider
    assert config.embedding_model
    assert isinstance(config.data_dir, Path)
    assert isinstance(config.corpus_dir, Path)
    assert isinstance(config.council_dir, Path)
    assert isinstance(config.plans_dir, Path)
    assert isinstance(config.chunk_max_size, int)
    assert isinstance(config.retrieval_top_k, int)
    assert config.chroma_collection


def test_load_config_resolves_paths_relative_to_config_file(
    tmp_path: Path,
) -> None:
    """Write a temp config with a relative data_dir; assert it resolves to absolute."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: mydata\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.data_dir.is_absolute()
    assert config.data_dir == (tmp_path / "mydata").resolve()


def test_load_config_raises_file_not_found_for_missing_file(
    tmp_path: Path,
) -> None:
    """Assert FileNotFoundError is raised when the config file does not exist."""
    missing = tmp_path / "nonexistent_config.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(missing)


def test_load_config_raises_on_missing_required_key(tmp_path: Path) -> None:
    """Write a config without the 'llm' section; assert KeyError is raised."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        # 'llm' section is intentionally omitted
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: data\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        load_config(config_file)


def test_load_config_includes_goals_fields(tmp_path: Path) -> None:
    """load_config resolves goals_dir, personas_dir, and goals_manifest_path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: data\n"
        "goals_dir: my_goals\n"
        "personas_dir: my_personas\n"
        "goals_manifest_path: my_manifest.json\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert isinstance(config.goals_dir, Path)
    assert config.goals_dir.is_absolute()
    assert config.goals_dir == (tmp_path / "my_goals").resolve()

    assert isinstance(config.personas_dir, Path)
    assert config.personas_dir.is_absolute()
    assert config.personas_dir == (tmp_path / "my_personas").resolve()

    assert isinstance(config.goals_manifest_path, Path)
    assert config.goals_manifest_path.is_absolute()
    assert config.goals_manifest_path == (tmp_path / "my_manifest.json").resolve()


def test_load_config_goals_fields_use_defaults(tmp_path: Path) -> None:
    """load_config uses defaults for goals_dir, personas_dir, goals_manifest_path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: data\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.goals_dir == (tmp_path / "goals").resolve()
    assert config.personas_dir == (tmp_path / "council").resolve()
    assert config.goals_manifest_path == (tmp_path / "goals_manifest.json").resolve()
