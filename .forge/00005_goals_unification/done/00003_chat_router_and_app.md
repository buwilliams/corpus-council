# Task 00003: Create chat router, update app.py, delete old routers

## Role
programmer

## Objective
Create `src/corpus_council/api/routers/chat.py` implementing `POST /chat`, update `src/corpus_council/api/app.py` to register only the new chat router (removing query/conversation/collection), and delete the three old router files from disk. After this task the app starts cleanly and `POST /chat` is the only conversational endpoint.

## Context

**Dependencies:**
- Task 00001 created `src/corpus_council/core/chat.py` with `run_goal_chat`
- Task 00002 added `ChatRequest` and `ChatResponse` to `src/corpus_council/api/models.py` and removed obsolete models

**Files to create:**
- `src/corpus_council/api/routers/chat.py`

**Files to modify:**
- `src/corpus_council/api/app.py`

**Files to DELETE from disk:**
- `src/corpus_council/api/routers/query.py`
- `src/corpus_council/api/routers/conversation.py`
- `src/corpus_council/api/routers/collection.py`

---

### chat.py router implementation

The router:
1. Validates `user_id` via `validate_id` — raises `HTTPException(status_code=422)` on failure
2. Validates `conversation_id` if supplied: check for `..` segments — raise `HTTPException(status_code=400, detail="Invalid conversation_id")` if found
3. Loads goal from manifest using `load_goal(request.goal, config.goals_manifest_path)` — raises `HTTPException(status_code=404)` if `ValueError` is raised
4. Generates a UUID `conversation_id` if not supplied: `str(uuid.uuid4())`
5. Calls `run_goal_chat(goal_name, user_id, conversation_id, message, config, store, llm, mode)` — `mode` defaults to `config.deliberation_mode` if not supplied
6. Returns `ChatResponse(response=resp, goal=request.goal, conversation_id=conv_id)`

**Import pattern** for `config`, `store`, `llm` (follow existing routers):
```python
from corpus_council.api.app import config, llm, store
```
Import this inside the function body (deferred import) to avoid circular imports — same pattern as `query.py`, `conversation.py`, `collection.py`.

**Exact `conversation_id` validation:**
```python
if request.conversation_id is not None and ".." in request.conversation_id:
    raise HTTPException(status_code=400, detail="Invalid conversation_id")
```

**`validate_id` for `user_id`:**
```python
from corpus_council.core.validation import validate_id
...
try:
    user_id = validate_id(request.user_id, "user_id")
except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc
```

**Goal loading (maps ValueError to 404):**
```python
from corpus_council.core.goals import load_goal
...
try:
    _goal_config = load_goal(request.goal, config.goals_manifest_path)
    _ = _goal_config  # goal existence confirmed; run_goal_chat loads it again internally
except ValueError as exc:
    raise HTTPException(status_code=404, detail=f"Goal {request.goal!r} not found") from exc
```

Actually, to avoid loading the goal twice, pass `goal_name` to `run_goal_chat` which handles goal loading internally. The router only needs to verify the goal exists beforehand to return 404 cleanly (before generating a conversation_id). `run_goal_chat` raises `KeyError` if the goal is not found — the router should catch `KeyError` from `run_goal_chat` too, as a safety net:
```python
try:
    resp, conv_id = run_goal_chat(
        goal_name=request.goal,
        user_id=user_id,
        conversation_id=conversation_id,
        message=request.message,
        config=config,
        store=store,
        llm=llm,
        mode=resolved_mode,
    )
except KeyError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
```

---

### app.py update

Current `app.py` imports and registers `query`, `conversation`, `collection`, `corpus`, `files`, `admin` routers.

New `app.py` must:
1. Import `chat` router instead of `query`, `conversation`, `collection`
2. Register `chat.router`, `corpus.router`, `files.router`, `admin.router` — in that order
3. `StaticFiles` mount stays at the bottom (after all router registrations)
4. Keep exception handlers unchanged
5. Keep `config`, `store`, `llm` module-level globals unchanged

The `from corpus_council.api.routers import (...)` block must be updated to only import `admin`, `chat`, `corpus`, `files`.

---

### app.py StaticFiles mount position

The StaticFiles mount must remain AFTER all `include_router` calls. In the current file, this is already handled by putting it at the bottom. Maintain this order.

---

### Deletion of old router files

Use `os.remove` or `Path.unlink` is not appropriate here — delete via shell. The three files to delete:
- `src/corpus_council/api/routers/query.py`
- `src/corpus_council/api/routers/conversation.py`
- `src/corpus_council/api/routers/collection.py`

---

**Tech stack:** Python 3.12, FastAPI, uv.

## Steps
1. Create `src/corpus_council/api/routers/chat.py` as described above, with `from __future__ import annotations`, full type annotations, and `__all__ = ["router"]`.
2. Update `src/corpus_council/api/app.py`:
   - Replace `from corpus_council.api.routers import (admin, collection, conversation, corpus, files, query,)` with `from corpus_council.api.routers import (admin, chat, corpus, files,)`
   - Replace the four `include_router` calls for query/conversation/collection with a single `app.include_router(chat.router)`
   - Keep `corpus.router`, `files.router`, `admin.router` registrations
3. Delete the three old router files from disk:
   ```bash
   rm src/corpus_council/api/routers/query.py
   rm src/corpus_council/api/routers/conversation.py
   rm src/corpus_council/api/routers/collection.py
   ```
4. Run `uv run python -c "from corpus_council.api.app import app"` and confirm no import error.
5. Run `uv run pytest` and confirm exit 0.
6. Run `uv run pyright src/` and confirm exit 0.
7. Run `uv run ruff check . && uv run ruff format --check .` and confirm exit 0.

## Verification
- File `src/corpus_council/api/routers/chat.py` exists
- `src/corpus_council/api/routers/chat.py` defines a `router` object and `POST /chat` handler
- File `src/corpus_council/api/routers/query.py` does NOT exist
- File `src/corpus_council/api/routers/conversation.py` does NOT exist
- File `src/corpus_council/api/routers/collection.py` does NOT exist
- `src/corpus_council/api/app.py` contains no reference to `query` router
- `src/corpus_council/api/app.py` contains no reference to `conversation` router
- `src/corpus_council/api/app.py` contains no reference to `collection` router
- `uv run pytest` exits 0
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged
- Dynamic: start, send POST /chat, verify response shape, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  RESP=$(curl -sf -X POST http://localhost:8765/chat \
    -H 'Content-Type: application/json' \
    -d '{"goal":"default","user_id":"testuser","message":"hello"}' 2>&1) || true
  echo "$RESP" | python3 -c "
  import sys, json
  data = json.load(sys.stdin)
  assert 'response' in data or 'detail' in data, f'Unexpected: {data}'
  print('POST /chat responded')
  "
  kill $APP_PID
  ```

## Done When
- [ ] `src/corpus_council/api/routers/chat.py` created and `POST /chat` responds
- [ ] Old router files deleted from disk
- [ ] `app.py` updated — only chat, corpus, files, admin routers registered
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/api/routers/chat.py src/corpus_council/api/app.py && git rm src/corpus_council/api/routers/query.py src/corpus_council/api/routers/conversation.py src/corpus_council/api/routers/collection.py && git commit -m "task-00003: create chat router, update app.py, delete old routers"
```
