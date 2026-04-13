from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig


@dataclass
class IngestResult:
    files_processed: int
    chunks_created: int


def _chunk_text(text: str, max_size: int) -> list[tuple[str, int, int]]:
    """Split text into chunks of at most max_size characters.

    Tries to split on paragraph boundaries (double newline). If a paragraph
    exceeds max_size, hard-splits it at max_size characters.

    Returns a list of (chunk_text, char_start, char_end) tuples where
    char_start and char_end are offsets in the original text.
    """
    chunks: list[tuple[str, int, int]] = []

    # Split on paragraph boundaries, tracking offsets
    paragraphs: list[tuple[str, int]] = []
    pos = 0
    for para in text.split("\n\n"):
        paragraphs.append((para, pos))
        pos += len(para) + 2  # +2 for the "\n\n" separator

    current_text = ""
    current_start = 0

    for para, para_offset in paragraphs:
        if not para:
            # Empty paragraph (e.g., leading/trailing \n\n); skip but note we
            # still advanced pos above, so offsets remain correct.
            continue

        # If adding this paragraph would not exceed max_size, accumulate it
        if current_text:
            candidate = current_text + "\n\n" + para
        else:
            candidate = para

        if len(candidate) <= max_size:
            if current_text:
                current_text = candidate
            else:
                current_text = para
                current_start = para_offset
        else:
            # Flush current accumulated text first
            if current_text:
                char_end = current_start + len(current_text)
                chunks.append((current_text, current_start, char_end))
                current_text = ""

            # Now handle this paragraph, which may itself exceed max_size
            para_text = para
            para_pos = para_offset
            while len(para_text) > max_size:
                segment = para_text[:max_size]
                chunks.append((segment, para_pos, para_pos + max_size))
                para_text = para_text[max_size:]
                para_pos += max_size

            # Whatever remains of the paragraph starts a new accumulation
            if para_text:
                current_text = para_text
                current_start = para_pos

    # Flush anything remaining
    if current_text:
        char_end = current_start + len(current_text)
        chunks.append((current_text, current_start, char_end))

    return chunks


def ingest_corpus(
    config: AppConfig, corpus_dir: Path | None = None
) -> IngestResult:
    """Ingest all .md and .txt files from corpus_dir (or config.corpus_dir).

    Splits each file into text chunks and writes chunk metadata as flat JSON
    files under config.chunks_dir / {source_hash} / {chunk_index}.json.

    Idempotent: if all chunk files for a file already exist, skips chunk
    creation but still counts the file in files_processed.

    Args:
        config: Application configuration.
        corpus_dir: Override corpus directory. When provided, used instead of
            config.corpus_dir.
    """
    resolved_corpus_dir = corpus_dir if corpus_dir is not None else config.corpus_dir
    chunks_root = config.chunks_dir
    chunks_root.mkdir(parents=True, exist_ok=True)

    files_processed = 0
    chunks_created = 0

    extensions = {".md", ".txt"}
    source_files = [
        p
        for p in resolved_corpus_dir.rglob("*")
        if p.is_file() and p.suffix in extensions
    ]

    for source_path in sorted(source_files):
        content = source_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(content.encode()).hexdigest()

        chunks = _chunk_text(content, config.chunk_max_size)
        hash_dir = chunks_root / source_hash

        # Check idempotency: all chunk files already exist?
        all_exist = hash_dir.exists() and all(
            (hash_dir / f"{i}.json").exists() for i in range(len(chunks))
        )

        files_processed += 1

        if all_exist:
            continue

        # Write chunks that don't exist yet
        hash_dir.mkdir(parents=True, exist_ok=True)
        relative_path = source_path.relative_to(resolved_corpus_dir)

        for chunk_index, (chunk_text, char_start, char_end) in enumerate(chunks):
            chunk_file = hash_dir / f"{chunk_index}.json"
            if chunk_file.exists():
                continue
            chunk_data = {
                "chunk_id": str(uuid.uuid4()),
                "source_file": str(relative_path),
                "source_hash": source_hash,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "char_start": char_start,
                "char_end": char_end,
            }
            chunk_file.write_text(
                json.dumps(chunk_data, ensure_ascii=False), encoding="utf-8"
            )
            chunks_created += 1

    return IngestResult(files_processed=files_processed, chunks_created=chunks_created)


__all__ = ["IngestResult", "ingest_corpus"]
