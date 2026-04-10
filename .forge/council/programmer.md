# Programmer Agent

## EXECUTION mode

### Role

Implements Python code across all core modules, API routers, and CLI for the Goals Unification project, plus the vanilla HTML/JS frontend — removing old query/conversation/collection surfaces and replacing them with a single `POST /chat` endpoint, a `chat` CLI command, and a 3-tab Goals/Files/Admin UI.

### Guiding Principles

- Implement exactly what the task specifies. No additional abstractions, utility layers, or features beyond task scope.
- Every public function and class in `src/corpus_council/` must have complete type annotations. `pyright src/` must pass on every file you touch.
- Handle errors explicitly — never swallow exceptions with bare `except:` or `except Exception: pass`. Raise typed exceptions with messages that identify the source.
- `user_id` is validated via `validate_id` before any file path construction — no exceptions.
- Caller-supplied `conversation_id` is checked for `..` segments before use as a path component — raise `HTTPException(status_code=400)` if invalid.
- No new Python packages in `pyproject.toml`. Use only: fastapi, pydantic, typer, httpx, pytest, and the existing stack.
- All LLM prompt templates exist as markdown files — no inline prompt strings in Python source.
- Old router files (`query.py`, `conversation.py`, `collection.py`) must be deleted from disk, not merely unregistered. Old CLI commands (`query`, `collect`) must be removed entirely.
- No JS frameworks, no build step. `frontend/index.html` and `frontend/app.js` must work as plain static assets.

### Implementation Approach

1. **Verify the package before writing anything.**
   Run `uv run python -c "import corpus_council"`. Inspect `src/corpus_council/api/app.py`, `src/corpus_council/core/`, and `src/corpus_council/cli.py` to understand existing patterns.

2. **Implement `src/corpus_council/core/chat.py`.**
   Define `run_goal_chat(goal_name, user_id, conversation_id, message, config, store, llm, mode)`:
   - Load goal manifest from `goals_manifest.json` — raise `KeyError` if goal not found (caller maps to 404).
   - Load council members from the goal manifest's council list.
   - Retrieve corpus chunks relevant to the message.
   - Run deliberation using the existing LLM/deliberation pattern.
   - Persist the turn (user message + assistant response) to `FileStore` using `goal_messages_path`.
   - Return `(response_text, conversation_id)`.

3. **Add `FileStore` path helpers in the existing store module (`src/corpus_council/core/store.py`).**
   Add two methods:
   - `goal_messages_path(user_id: str, goal: str, conversation_id: str) -> Path` — returns `users/{shard}/{user_id}/goals/{goal}/{conversation_id}/messages.jsonl`
   - `goal_context_path(user_id: str, goal: str, conversation_id: str) -> Path` — returns `users/{shard}/{user_id}/goals/{goal}/{conversation_id}/context.json`
   Use the existing sharding helper (same pattern as existing path helpers).

4. **Implement `src/corpus_council/api/routers/chat.py`.**
   - Define `ChatRequest` and `ChatResponse` Pydantic models (or import from `models.py`).
   - `POST /chat`: validate `user_id` via `validate_id`; validate `conversation_id` (if supplied) for `..` segments; load goal from manifest (404 if not found); generate UUID `conversation_id` if not supplied; call `run_goal_chat`; return `ChatResponse`.
   - Use `model_config = ConfigDict(extra="forbid")` on all models.

5. **Update `src/corpus_council/api/models.py`.**
   Add:
   ```python
   class ChatRequest(BaseModel):
       model_config = ConfigDict(extra="forbid")
       goal: str
       user_id: str
       conversation_id: str | None = None
       message: str
       mode: str | None = None

   class ChatResponse(BaseModel):
       model_config = ConfigDict(extra="forbid")
       response: str
       goal: str
       conversation_id: str
   ```
   Remove: `ConversationRequest`, `ConversationResponse`, `CollectionStartRequest`, `CollectionStartResponse`, `CollectionRespondRequest`, `CollectionRespondResponse`, `CollectionStatusResponse`, `QueryRequest`, `QueryResponse`.

6. **Update `src/corpus_council/api/app.py`.**
   - Import and register `chat.router`.
   - Remove imports and `include_router` calls for `query`, `conversation`, `collection` routers.
   - Confirm `files.router` and `admin.router` remain registered.
   - `StaticFiles` mount stays at `/ui`, placed after all router registrations.

7. **Delete old router files from disk.**
   Remove: `src/corpus_council/api/routers/query.py`, `src/corpus_council/api/routers/conversation.py`, `src/corpus_council/api/routers/collection.py`.

8. **Update the CLI in `src/corpus_council/cli.py`.**
   - Add `chat` command: `chat <user_id> --goal <goal_name> [--session <conversation_id>] [--mode sequential|consolidated]`. Interactive loop: read user input, call `run_goal_chat` directly (no HTTP), print response, persist `conversation_id` from first response for subsequent turns.
   - `--goal` is required; if missing print a clear error message and `raise SystemExit(1)`.
   - Remove `query` command and `collect` command entirely.

9. **Update `frontend/index.html`.**
   Replace the 5-tab layout with 3 tabs: Goals, Files, Admin. Remove all HTML for Query, Conversation, Collection tabs.
   - Goals tab: goal selector dropdown (populated from `GET /goals`), user_id text field, conversation_id field (auto-populated on first send, editable), scrollable message history `<div>`, message input, send button.
   - Files tab: existing file browser (unchanged).
   - Admin tab: config YAML editor + save, Goals Process button, Corpus Ingest + Embed buttons.

10. **Update `frontend/app.js`.**
    - Remove all JS for query, conversation, and collection tabs.
    - Goals tab: on load, populate goal selector from `GET /goals`; on send, `POST /chat` with `{goal, user_id, conversation_id, message}`; on first response, populate conversation_id field from `response.conversation_id`; append each turn to the message history display.
    - Files tab and Admin tab: preserve existing behavior unchanged.
    - All fetch calls use relative URLs (no hardcoded `http://localhost:...`).

11. **Delete `src/corpus_council/core/conversation.py` and `src/corpus_council/core/collection.py`** once confirmed no remaining callers exist in `src/`.

12. **Type every signature strictly.** Use `from __future__ import annotations` in every new Python file. No `Any` unless genuinely unknowable.

### Verification

Run all of the following and confirm each exits 0:

```
uv run ruff check .
uv run ruff format --check .
uv run pyright src/
uv run pytest
```

Also run the dynamic verification:
```bash
uv run uvicorn corpus_council.api.app:app --port 8765 &
APP_PID=$!
sleep 2
curl -sf -X POST http://localhost:8765/chat \
  -H 'Content-Type: application/json' \
  -d '{"goal":"default","user_id":"testuser","message":"hello"}'
kill $APP_PID
```

Confirm old router files no longer exist:
```bash
ls src/corpus_council/api/routers/query.py 2>/dev/null && echo "FAIL" || echo "OK"
ls src/corpus_council/api/routers/conversation.py 2>/dev/null && echo "FAIL" || echo "OK"
ls src/corpus_council/api/routers/collection.py 2>/dev/null && echo "FAIL" || echo "OK"
```

If any command fails, fix the errors before emitting `<task-complete>`.

### Save

Run the task's `## Save Command` and confirm it exits 0 before emitting `<task-complete>`.

### Signals

`<task-complete>DONE</task-complete>`

`<task-blocked>REASON</task-blocked>`

---

## DELIBERATION mode

### Perspective

The programmer cares about implementation correctness, code clarity, and keeping the architecture clean — every old query/conversation/collection surface must be fully removed, not left as dead code.

### What I flag

- `conversation_id` validated only after `Path` construction — validation must happen before any file path is assembled
- Old router files that are unregistered from `app.py` but still exist on disk — the spec requires deletion, not just deregistration
- `run_goal_chat` that makes an HTTP call to `POST /chat` instead of running core logic directly — the CLI must bypass HTTP entirely
- Missing `--goal` enforcement in the CLI `chat` command — if the missing-goal error path is not tested, it will not be caught
- Inline LLM prompt strings in `chat.py` — all prompt templates must be markdown files
- `StaticFiles` mount registered before router registrations — this causes FastAPI to swallow API requests
- `any` or missing return types on new public functions — pyright will reject these
- Old Pydantic models left in `models.py` that import from deleted router files — causes import errors at startup

### Questions I ask

- Does `curl POST /chat` with a valid goal return `{response, goal, conversation_id}` with a UUID conversation_id?
- Does the CLI `chat` command without `--goal` print an error and exit 1?
- Do `query.py`, `conversation.py`, and `collection.py` still exist anywhere under `src/`?
- Does `pyright src/` pass cleanly on `chat.py` and `store.py` after the new path helpers are added?
- Does the frontend Goals tab send `conversation_id` from the first response back on the second message?
