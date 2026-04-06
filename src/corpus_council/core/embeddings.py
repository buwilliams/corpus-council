from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import chromadb
import chromadb.api.models.Collection

from .config import AppConfig


@dataclass
class EmbedResult:
    vectors_created: int


def _load_all_chunks(config: AppConfig) -> list[dict[str, Any]]:
    """Glob all chunk JSON files from config.data_dir / 'chunks' / '**/*.json'."""
    chunks_root = config.data_dir / "chunks"
    chunks: list[dict[str, Any]] = []
    for json_path in sorted(chunks_root.glob("**/*.json")):
        raw: Any = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            chunks.append(raw)
    return chunks


def _get_chroma_collection(
    config: AppConfig,
) -> chromadb.api.models.Collection.Collection:
    """Return the ChromaDB collection, creating it if needed."""
    client = chromadb.PersistentClient(path=str(config.data_dir / "embeddings"))
    collection: chromadb.api.models.Collection.Collection = (
        client.get_or_create_collection(config.chroma_collection)
    )
    return collection


def embed_corpus(config: AppConfig) -> EmbedResult:
    """Embed all corpus chunks and upsert them into ChromaDB.

    Loads chunk JSON files written by ingest_corpus, encodes texts with the
    configured embedding provider, and upserts each chunk into the ChromaDB
    collection identified by config.chroma_collection.

    Raises:
        ValueError: if config.embedding_provider is not supported.
    """
    if config.embedding_provider != "sentence-transformers":
        raise ValueError(f"Unknown embedding provider: {config.embedding_provider}")

    chunks = _load_all_chunks(config)
    if not chunks:
        return EmbedResult(vectors_created=0)

    # Import here so an unsupported provider never requires sentence_transformers
    import logging

    from sentence_transformers import SentenceTransformer

    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    model: SentenceTransformer = SentenceTransformer(
        config.embedding_model, local_files_only=True
    )

    texts: list[str] = [str(c.get("text", "")) for c in chunks]
    raw_embeddings: Any = model.encode(texts, show_progress_bar=False)

    # raw_embeddings is a numpy 2-D array; each row is a numpy vector.
    # ChromaDB's Embeddings type accepts list[Sequence[float]].
    embeddings: list[Sequence[float]] = [row.tolist() for row in raw_embeddings]

    ids: list[str] = [str(c["chunk_id"]) for c in chunks]
    documents: list[str] = texts
    metadatas: list[dict[str, Any]] = [
        {
            "source_file": str(c.get("source_file", "")),
            "chunk_index": int(c.get("chunk_index", 0)),
        }
        for c in chunks
    ]

    collection = _get_chroma_collection(config)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,  # type: ignore[arg-type]  # dict[str, Any] satisfies Metadata
    )

    return EmbedResult(vectors_created=len(chunks))


__all__ = ["EmbedResult", "embed_corpus"]
