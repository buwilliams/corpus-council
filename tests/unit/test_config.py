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


@pytest.mark.parametrize(
    "removed_key",
    ["goals_dir", "personas_dir", "goals_manifest_path", "corpus_dir", "council_dir"],
)
def test_load_config_raises_on_removed_key(tmp_path: Path, removed_key: str) -> None:
    """load_config raises ValueError when a removed config key is present in YAML."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: data\n"
        f"{removed_key}: some_value\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=f"Config key {removed_key!r} is no longer supported"):
        load_config(config_file)


def test_all_derived_paths_resolve_from_data_dir(tmp_path: Path) -> None:
    """All eight derived properties equal (config_dir / data_dir / subdir).resolve()."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: testroot\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )

    config = load_config(config_file)
    data_dir = (tmp_path / "testroot").resolve()

    assert config.corpus_dir == data_dir / "corpus"
    assert config.council_dir == data_dir / "council"
    assert config.goals_dir == data_dir / "goals"
    assert config.personas_dir == data_dir / "council"
    assert config.goals_manifest_path == data_dir / "goals_manifest.json"
    assert config.chunks_dir == data_dir / "chunks"
    assert config.embeddings_dir == data_dir / "embeddings"
    assert config.users_dir == data_dir / "users"


def test_personas_dir_equals_council_dir() -> None:
    """Directly constructed AppConfig: personas_dir and council_dir are identical."""
    config = AppConfig(
        llm_provider="x",
        llm_model="x",
        embedding_provider="x",
        embedding_model="x",
        data_dir=Path("/tmp/test"),
        chunk_max_size=512,
        retrieval_top_k=5,
    )

    assert config.personas_dir == config.council_dir


def test_chunks_dir_and_embeddings_dir_and_users_dir_derived() -> None:
    """Directly constructed AppConfig: chunks_dir, embeddings_dir, users_dir are correct."""
    data_dir = Path("/tmp/mydata")
    config = AppConfig(
        llm_provider="x",
        llm_model="x",
        embedding_provider="x",
        embedding_model="x",
        data_dir=data_dir,
        chunk_max_size=512,
        retrieval_top_k=5,
    )

    assert config.chunks_dir == data_dir / "chunks"
    assert config.embeddings_dir == data_dir / "embeddings"
    assert config.users_dir == data_dir / "users"


def test_load_config_derived_paths_come_from_data_dir(tmp_path: Path) -> None:
    """Derived path properties are rooted at data_dir, not config_dir."""
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
    data_dir = (tmp_path / "data").resolve()

    assert config.goals_dir == data_dir / "goals"
    assert config.personas_dir == data_dir / "council"
    assert config.goals_manifest_path == data_dir / "goals_manifest.json"
    assert config.corpus_dir == data_dir / "corpus"
    assert config.council_dir == data_dir / "council"
    assert config.chunks_dir == data_dir / "chunks"
    assert config.embeddings_dir == data_dir / "embeddings"
    assert config.users_dir == data_dir / "users"
