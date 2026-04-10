# Task 00003 — Register routers and mount StaticFiles in `app.py`

## Agent
programmer

## Goal
Update `src/corpus_council/api/app.py` to register the four currently-unregistered routers
(`conversation`, `collection`, `files`, `admin`) and mount the `frontend/` directory at `/ui`.

## Prerequisites
- Task 00001 (`files.py`) must be complete
- Task 00002 (`admin.py`) must be complete
- Task 00004 (`frontend/` files) is NOT required — the mount will silently work once the
  directory exists; if it does not yet exist FastAPI will raise at startup, but the test
  suite uses a different `StaticFiles` strategy (see Implementation Notes).

## Current state of `src/corpus_council/api/app.py`

```python
from corpus_council.api.routers import corpus, query  # noqa: E402

app.include_router(query.router)
app.include_router(corpus.router)
```

## Deliverables

Edit `src/corpus_council/api/app.py` to produce the following state after the existing
`app.include_router(corpus.router)` line:

```python
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
app.include_router(conversation.router)
app.include_router(collection.router)
app.include_router(files.router)
app.include_router(admin.router)
```

Then, at the **end** of `app.py` (after all exception handlers and `__all__`), add the
StaticFiles mount:

```python
from pathlib import Path as _Path  # noqa: E402

from fastapi.staticfiles import StaticFiles  # noqa: E402

_frontend_dir = _Path("frontend")
if _frontend_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="ui")
```

The `if _frontend_dir.is_dir()` guard prevents a `RuntimeError` when the test suite
runs before `frontend/` has been created (task 00004 creates it). This is the correct
pattern: the mount is optional during development and tests, and mandatory in deployment.

## Implementation Notes

- The `StaticFiles` mount **must** come after all `include_router` calls — FastAPI matches
  routes top-to-bottom and the static mount would shadow any API route whose path begins
  with `/ui` if placed first.
- `html=True` enables serving `index.html` for directory requests (e.g. `GET /ui/` returns
  `frontend/index.html`).
- Do not change the existing exception handlers or the `load_config` / `LLMClient` /
  `FileStore` initialization lines.

## Verification

```bash
ruff check src/
ruff format --check src/
pyright src/
uv run python -c "from corpus_council.api.app import app; print('app import ok')"
```

All must exit 0 / print `app import ok`.

## Save Command

```bash
uv run python -c "
from corpus_council.api.app import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
assert '/conversation' in routes, f'conversation missing, got {routes}'
assert '/collection/start' in routes, f'collection missing, got {routes}'
assert '/files' in routes, f'files missing, got {routes}'
assert '/config' in routes, f'admin missing, got {routes}'
print('all routers registered')
"
```

Must print `all routers registered` and exit 0.
