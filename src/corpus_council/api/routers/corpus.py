from __future__ import annotations

import dataclasses
from pathlib import Path

from fastapi import APIRouter

from corpus_council.api.models import (
    CorpusEmbedResponse,
    CorpusIngestRequest,
    CorpusIngestResponse,
)
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
from corpus_council.core.validation import validate_path_containment

router = APIRouter()


@router.post("/corpus/ingest", response_model=CorpusIngestResponse)
async def post_corpus_ingest(request: CorpusIngestRequest) -> CorpusIngestResponse:
    """POST /corpus/ingest — ingest corpus files from the given path."""
    from corpus_council.api.app import config

    validated_path = validate_path_containment(
        Path(request.path), config.corpus_dir, "corpus path"
    )
    modified_config = dataclasses.replace(config, corpus_dir=validated_path)
    result = ingest_corpus(modified_config)
    return CorpusIngestResponse(
        chunks_created=result.chunks_created,
        files_processed=result.files_processed,
    )


@router.post("/corpus/embed", response_model=CorpusEmbedResponse)
async def post_corpus_embed() -> CorpusEmbedResponse:
    """POST /corpus/embed — embed all corpus chunks into the vector store."""
    from corpus_council.api.app import config

    result = embed_corpus(config)
    return CorpusEmbedResponse(vectors_created=result.vectors_created)


__all__ = ["router"]
