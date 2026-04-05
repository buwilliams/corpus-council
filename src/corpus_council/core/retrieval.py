from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .config import AppConfig
from .embeddings import _get_chroma_collection


@dataclass
class ChunkResult:
    chunk_id: str
    text: str
    source_file: str
    chunk_index: int
    distance: float


def retrieve_chunks(
    query: str,
    config: AppConfig,
    top_k: int | None = None,
) -> list[ChunkResult]:
    """Embed query and return the top-K most similar corpus chunks from ChromaDB.

    Args:
        query: The user query text to embed and search.
        config: Application configuration.
        top_k: Number of results to return. Defaults to config.retrieval_top_k.

    Raises:
        ValueError: if config.embedding_provider is not supported.
    """
    if config.embedding_provider != "sentence-transformers":
        raise ValueError(f"Unknown embedding provider: {config.embedding_provider}")

    n_results = top_k if top_k is not None else config.retrieval_top_k

    import logging

    from sentence_transformers import SentenceTransformer

    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    model: SentenceTransformer = SentenceTransformer(config.embedding_model, local_files_only=True)
    raw_embedding: Any = model.encode([query], show_progress_bar=False)
    query_vector: Sequence[float] = raw_embedding[0].tolist()

    collection = _get_chroma_collection(config)
    results: Any = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[ChunkResult] = []
    ids_list: list[str] = results["ids"][0] if results["ids"] else []
    docs_list: list[str] = results["documents"][0] if results["documents"] else []
    metas_list: list[dict[str, Any]] = (
        results["metadatas"][0] if results["metadatas"] else []
    )
    dists_list: list[float] = results["distances"][0] if results["distances"] else []

    for chunk_id, text, meta, distance in zip(
        ids_list, docs_list, metas_list, dists_list
    ):
        hits.append(
            ChunkResult(
                chunk_id=str(chunk_id),
                text=str(text),
                source_file=str(meta.get("source_file", "")),
                chunk_index=int(meta.get("chunk_index", 0)),
                distance=float(distance),
            )
        )

    return hits


__all__ = ["ChunkResult", "retrieve_chunks"]
