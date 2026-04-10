# Project Spec: Goals Unification

## Goal

Correct the architectural misalignment between the goals model (established in 00003_goals) and the current REST API, CLI, and frontend UI. All three surfaces currently expose a fragmented model — separate endpoints and commands for query (goal-aware, stateless), conversation (stateful, no goal), and collection (obsolete plan-based). None of this aligns with the goals model, which states any interaction is expressed as a goal. When this project is complete: the REST API exposes a single `POST /chat` endpoint (stateful, goal-aware); the CLI has a single `chat` command requiring `--goal`; and the frontend has three tabs — Goals, Files, and Admin — with no trace of the old query/conversation/collection concepts.

## Why This Matters

Spec 00003_goals explicitly stated: "any interaction is expressed as a goal, and the core system has no hardcoded notion of 'collection mode' or 'conversation mode.'" The frontend (00004_simple_frontend) was built before this was fully surfaced, and the API and CLI were never updated. All three interfaces now present a misleading, contradictory model to operators and integrators. Correcting all three surfaces together ensures the system is coherent across every entry point.

## Deliverables

### REST API

- [ ] `POST /chat` endpoint: accepts `{goal, user_id, conversation_id (optional), message, mode (optional)}`; returns `{response, goal, conversation_id}`; stateful (persists turns via `FileStore`) and goal-aware (loads council and corpus from goal manifest)
- [ ] New `src/corpus_council/api/routers/chat.py` router registered in `app.py`
- [ ] New Pydantic models `ChatRequest` and `ChatResponse` in `models.py`
- [ ] Remove `POST /query`, `POST /conversation`, `POST /collection/start`, `POST /collection/respond`, `GET /collection/{user_id}/{session_id}`
- [ ] Delete router files `query.py`, `conversation.py`, `collection.py`
- [ ] Remove obsolete Pydantic models: `ConversationRequest`, `ConversationResponse`, `CollectionStartRequest`, `CollectionStartResponse`, `CollectionRespondRequest`, `CollectionRespondResponse`, `CollectionStatusResponse`, `QueryRequest`, `QueryResponse`

### CLI

- [ ] Unified `chat <user_id> --goal <goal_name> [--session <conversation_id>] [--mode sequential|consolidated]` interactive command — stateful, goal-aware, uses `run_goal_chat` directly (no HTTP)
- [ ] Remove `query` command (was goal-aware but stateless)
- [ ] Remove `collect` command (was plan-based, obsolete)
- [ ] `--goal` is required for `chat`; missing goal prints a clear error and exits 1
- [ ] `--session` accepts an existing `conversation_id` to resume a prior conversation

### UI (frontend)

- [ ] Replace the current 5-tab layout (Query, Conversation, Collection, Files, Admin) with 3 tabs: Goals, Files, Admin
- [ ] **Goals tab**: goal selector dropdown (populated from `GET /goals`), user_id text field, conversation_id field (auto-populated on first send, editable to resume), scrollable message history, message input, send button; each turn displays user message and assistant response
- [ ] **Files tab**: existing file browser (functionally unchanged)
- [ ] **Admin tab**: config YAML editor + save, Goals Process button, Corpus Ingest + Embed buttons (existing admin functionality preserved)
- [ ] Remove all JS code for query, conversation, and collection tabs
- [ ] `POST /chat` is the only conversational API call made by the frontend

### Core

- [ ] New `src/corpus_council/core/chat.py` with `run_goal_chat(goal_name, user_id, conversation_id, message, config, store, llm, mode)` function
- [ ] `FileStore` path helpers: `goal_messages_path(user_id, goal, conversation_id)` and `goal_context_path(user_id, goal, conversation_id)` — sharded under `users/{shard}/{user_id}/goals/{goal}/{conversation_id}/`
- [ ] Delete `core/conversation.py` and `core/collection.py` once confirmed no remaining callers in `src/`

### Tests

- [ ] Integration tests for `POST /chat`: first message (auto-generates conversation_id), continuation (same conversation_id), unknown goal → 404, invalid user_id → 422
- [ ] Unit tests: new `FileStore` path helpers; `run_goal_chat` (LLM may be mocked in unit tests)
- [ ] Remove integration tests for the three deleted endpoints

## Tech Stack

- Language: Python 3.12
- Runtime / Platform: FastAPI + uvicorn (existing)
- Frontend: vanilla HTML/JS, Pico.css via CDN (existing)
- Key dependencies: existing only — fastapi, pydantic, typer, httpx (tests), pytest
- Build tool / package manager: uv

## Architecture Overview

`POST /chat` validates `user_id` via `validate_id`, loads the named goal from `goals_manifest.json` (404 if not found), generates a `conversation_id` (UUID) if not provided, loads council members, retrieves corpus chunks, runs deliberation, and persists the turn to `FileStore`. Core logic lives in `core/chat.py`. The `chat.py` router is a thin dispatch layer. The CLI `chat` command calls `run_goal_chat` directly — no HTTP round-trip. The frontend Goals tab calls `POST /chat` for every message turn, sending back the `conversation_id` received from the first response to maintain thread continuity.

## Testing Requirements

- Integration tests: `POST /chat` via `httpx.AsyncClient + ASGITransport`, `asyncio_mode = "auto"`; no mocking of `FileStore`, goal loading, or corpus retrieval
- Unit tests: `FileStore` new path helpers; `run_goal_chat` with mocked `LLMClient`
- Test framework: pytest
- Coverage threshold: all new public functions covered
- What must never be mocked (integration tests): `FileStore`, goal manifest loading, corpus retrieval pipeline

## Code Quality

- Linter: ruff (`uv run ruff check .` exits 0)
- Formatter: ruff format (`uv run ruff format --check .` exits 0)
- Type checking: pyright (`uv run pyright src/` exits 0)
- Tests: `uv run pytest` exits 0

## Constraints

- No new Python packages — `pyproject.toml` dependencies unchanged
- `conversation_id` is always a UUID string; auto-generated via `str(uuid.uuid4())` when not supplied
- `validate_id` called on `user_id` before any file path construction
- Caller-supplied `conversation_id` validated against path traversal (no `..` segments) before use in `FileStore`
- Frontend: vanilla HTML/JS only — no npm, bundler, or CDN links beyond existing Pico.css
- Old router files deleted from disk, not merely unregistered
- `--mode consolidated|sequential` continues to work via the new endpoint and CLI command

## Performance Requirements

None beyond existing baselines.

## Security Considerations

- `user_id` validated via `validate_id` before use in file path construction
- `goal` name validated against the manifest — unknown goals return 404 before file I/O
- Caller-supplied `conversation_id` checked for `..` segments before use as a path component

## Out of Scope

- Migrating existing conversation history from old per-user format to the new goal-keyed format
- Authentication, authorization, or session tokens
- WebSocket or streaming responses
- A `GET /chat/{user_id}/{goal}/{conversation_id}` history retrieval endpoint
- Changes to goals process step, corpus ingestion, or embedding pipeline

## Open Questions

None.

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- No new Python packages — `pyproject.toml` dependencies must remain unchanged
- No hardcoded behavioral rules, personas, or domain logic in Python source — all such rules live in council persona markdown files
- All LLM prompt templates must exist as markdown files — no inline prompt strings in Python source
- No relational database, message queue, or external service dependency — flat files and ChromaDB only
- `uv run ruff check .` exits 0 with no errors
- `uv run ruff format --check .` exits 0 with no errors
- `uv run pyright src/` exits 0 with no errors
- Old router files (`query.py`, `conversation.py`, `collection.py`) must be deleted from disk, not merely unregistered from the app
- `user_id` must be validated via `validate_id` before any file path construction; caller-supplied `conversation_id` checked for `..` segments before use as a path component
- No test stubs or smoke-tests in integration tests — `FileStore`, goal manifest loading, and corpus retrieval must not be mocked in integration tests

## Dynamic Verification
- **Exercise command:** `uv run uvicorn corpus_council.api.app:app --port 8765 & APP_PID=$! && sleep 2 && curl -sf -X POST http://localhost:8765/chat -H 'Content-Type: application/json' -d '{"goal":"default","user_id":"testuser","message":"hello"}' && kill $APP_PID`
- **Ready check:** `curl -sf http://localhost:8765/goals`
- **Teardown:** `kill $APP_PID`

## Execution
- **Test:** `uv run pytest`
- **Typecheck:** `uv run pyright src/`
- **Lint:** `uv run ruff check . && uv run ruff format --check .`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `uv run pytest` exits 0. `uv run pyright src/` exits 0. `uv run ruff check .` exits 0. The old router files (`query.py`, `conversation.py`, `collection.py`) do not exist under `src/`. `GET /goals` and `POST /chat` are the only conversational endpoints registered in the running app.
- **Max task tries:** 3
