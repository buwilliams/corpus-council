from __future__ import annotations

import json
from pathlib import Path

from corpus_council.core.config import AppConfig
from corpus_council.core.corpus import ingest_corpus

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path, chunk_max_size: int = 512) -> AppConfig:
    """Build an AppConfig entirely from tmp_path-based directories."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-20241022",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=data_dir,
        corpus_dir=corpus_dir,
        council_dir=tmp_path / "council",
        plans_dir=tmp_path / "plans",
        chunk_max_size=chunk_max_size,
        retrieval_top_k=5,
        chroma_collection="test_corpus",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ingest_corpus_processes_md_and_txt_files(tmp_path: Path) -> None:
    """2 .md files + 1 .txt file should result in files_processed == 3."""
    config = _make_config(tmp_path)
    (config.corpus_dir / "doc1.md").write_text(
        "# Doc 1\n\nContent one.", encoding="utf-8"
    )
    (config.corpus_dir / "doc2.md").write_text(
        "# Doc 2\n\nContent two.", encoding="utf-8"
    )
    (config.corpus_dir / "notes.txt").write_text("Plain text notes.", encoding="utf-8")

    result = ingest_corpus(config)

    assert result.files_processed == 3


def test_ingest_corpus_ignores_non_corpus_files(tmp_path: Path) -> None:
    """Non-.md/.txt files (.pdf, .py) should not be counted in files_processed."""
    config = _make_config(tmp_path)
    (config.corpus_dir / "real.md").write_text(
        "# Real\n\nActual content.", encoding="utf-8"
    )
    (config.corpus_dir / "ignored.pdf").write_bytes(b"%PDF-1.4 fake content")
    (config.corpus_dir / "script.py").write_text("print('hello')", encoding="utf-8")

    result = ingest_corpus(config)

    assert result.files_processed == 1


def test_ingest_corpus_creates_chunk_json_files(tmp_path: Path) -> None:
    """Chunk JSON files should exist at data/chunks/{hash}/{index}.json."""
    config = _make_config(tmp_path)
    (config.corpus_dir / "article.md").write_text(
        "# Article\n\nSome content here.", encoding="utf-8"
    )

    result = ingest_corpus(config)

    chunks_root = config.data_dir / "chunks"
    assert chunks_root.exists(), "chunks root directory should be created"

    # Find all chunk files
    chunk_files = list(chunks_root.rglob("*.json"))
    assert len(chunk_files) == result.chunks_created
    assert result.chunks_created > 0


def test_ingest_corpus_chunks_respect_max_size(tmp_path: Path) -> None:
    """A 2000-char doc with max_size=200 produces multiple chunks, each <= 200 chars."""
    config = _make_config(tmp_path, chunk_max_size=200)
    # No double-newlines to force hard splits at max_size boundaries
    long_text = "A" * 2000
    (config.corpus_dir / "long.txt").write_text(long_text, encoding="utf-8")

    result = ingest_corpus(config)

    assert result.chunks_created > 1, "should produce multiple chunks"

    # Verify each chunk text is within the max_size limit
    chunks_root = config.data_dir / "chunks"
    for chunk_file in chunks_root.rglob("*.json"):
        chunk_data = json.loads(chunk_file.read_text(encoding="utf-8"))
        assert len(chunk_data["text"]) <= 200, (
            f"chunk text length {len(chunk_data['text'])} exceeds max_size 200"
        )


def test_ingest_corpus_is_idempotent(tmp_path: Path) -> None:
    """Second run of ingest_corpus on same corpus should have chunks_created == 0."""
    config = _make_config(tmp_path)
    (config.corpus_dir / "repeat.md").write_text(
        "# Repeated\n\nThis file is processed twice.", encoding="utf-8"
    )

    first_result = ingest_corpus(config)
    second_result = ingest_corpus(config)

    assert first_result.chunks_created > 0
    assert second_result.chunks_created == 0
    assert second_result.files_processed == first_result.files_processed


def test_chunk_json_has_required_fields(tmp_path: Path) -> None:
    """Every chunk JSON file must contain all 7 required fields."""
    required_fields = {
        "chunk_id",
        "source_file",
        "source_hash",
        "chunk_index",
        "text",
        "char_start",
        "char_end",
    }
    config = _make_config(tmp_path)
    (config.corpus_dir / "fields_test.md").write_text(
        "# Fields Test\n\nContent to verify chunk fields.", encoding="utf-8"
    )

    ingest_corpus(config)

    chunks_root = config.data_dir / "chunks"
    chunk_files = list(chunks_root.rglob("*.json"))
    assert chunk_files, "at least one chunk file should exist"

    for chunk_file in chunk_files:
        chunk_data = json.loads(chunk_file.read_text(encoding="utf-8"))
        missing = required_fields - set(chunk_data.keys())
        assert not missing, f"chunk file {chunk_file.name} is missing fields: {missing}"
