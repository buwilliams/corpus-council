from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from corpus_council.core.config import load_config
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore

app = FastAPI(title="Corpus Council")

config = load_config(Path("config.yaml"))
store = FileStore(config.data_dir)
llm = LLMClient(config)

from corpus_council.api.routers import (  # noqa: E402
    admin,
    collection,
    conversation,
    corpus,
    files,
    query,
)

app.include_router(query.router)
app.include_router(corpus.router)
app.include_router(files.router)
app.include_router(conversation.router)
app.include_router(collection.router)
app.include_router(admin.router)


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(
    request: Request, exc: FileNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "Resource not found"})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    print(f"Internal server error: {exc}", file=sys.stderr)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


__all__ = ["app", "config", "store", "llm"]

from pathlib import Path as _Path  # noqa: E402

from fastapi.staticfiles import StaticFiles  # noqa: E402  # noqa: E402

_frontend_dir = _Path("frontend")
if _frontend_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="ui")
