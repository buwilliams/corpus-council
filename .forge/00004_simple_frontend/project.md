# Project Spec: Simple Frontend

## Goal

A vanilla HTML/JS single-page web application served by the existing FastAPI server that
exposes all Corpus Council features through a tabbed UI. Users of a deployed Corpus Council
instance can interact via Query, Conversation, and Collection modes, and administrators can
manage the filesystem (corpus, council, plans, goals, templates directories), edit
config.yaml, and trigger background operations (ingest, embed, process goals) — all without
touching the CLI.

## Why This Matters

Corpus Council's API is powerful but requires clients to build their own integration.
A lightweight reference frontend lowers the barrier for deployers evaluating the platform
and for end users who don't have a custom integration. It also serves as a living example
of how the API is meant to be consumed. Without it, every deployment that wants any UI
must build one from scratch.

## Deliverables

- [ ] `frontend/index.html` — single-page app with five tabs: Query, Conversation, Collection, Files, Admin
- [ ] `frontend/app.js` — all client-side logic, no framework, no build step
- [ ] `frontend/style.css` — minimal custom overrides on top of Pico.css (single CDN link)
- [ ] FastAPI `StaticFiles` mount serving `frontend/` at `/ui`
- [ ] New API router: `src/corpus_council/api/routers/files.py` — file management endpoints
- [ ] New API router: `src/corpus_council/api/routers/admin.py` — config read/write and goals process trigger
- [ ] Conversation and collection routers registered in `app.py`
- [ ] Integration tests for all new API endpoints

## Tech Stack

- Language: Python (backend additions), HTML5 / ES6+ JS (frontend)
- Runtime / Platform: FastAPI + Uvicorn (existing)
- Key dependencies: `fastapi.staticfiles.StaticFiles` (already in FastAPI), Pico.css via CDN (no backend dependency)
- Build tool: none — frontend files are served as-is
- Package manager: uv (existing)

## Architecture Overview

`frontend/` is a directory of static files mounted onto the FastAPI app via `StaticFiles`.
The HTML/JS calls the REST API at the same origin using relative URLs. No separate server
process.

Five tabs:

1. **Query** — POST /query; goal selector populated from goals manifest, mode selector
   (sequential/consolidated), response display
2. **Conversation** — POST /conversation; multi-turn chat; user_id from localStorage or
   input field; mode selector
3. **Collection** — POST /collection/start + /collection/respond; plan selector populated
   from plans directory listing; session state tracked in JS
4. **Files** — directory tree for corpus/, council/, plans/, goals/, templates/; click to
   view/edit text files; create new files; delete files
5. **Admin** — config.yaml editor (GET/PUT /config); trigger buttons for Ingest, Embed,
   and Process Goals with result display; links to existing /corpus/ingest and /corpus/embed

New API surface:
- `GET /files` — list the five managed root directories
- `GET /files/{path}` — list directory contents or return file text
- `POST /files/{path}` — create new file with text body
- `PUT /files/{path}` — overwrite file content
- `DELETE /files/{path}` — delete file
- `GET /config` — read config.yaml as text
- `PUT /config` — write config.yaml from text body
- `POST /admin/goals/process` — trigger goals processing (maps to existing `process_goals()`)

Existing endpoints reused as-is: `POST /corpus/ingest`, `POST /corpus/embed`.

## Testing Requirements

- Unit tests: none for frontend JS
- Integration tests: all new API endpoints (files router, admin router, config endpoints)
  covered by at least one integration test each; use a real temp directory — do not mock
  filesystem operations
- Test framework: pytest (existing)
- Coverage threshold: all new endpoints have at least one passing integration test

## Code Quality

- Linter / static analysis: ruff (existing)
- Formatter: ruff format (existing)
- Type checking: pyright (existing)
- Commands that must exit 0: `ruff check src/`, `ruff format --check src/`, `pyright src/`

## Constraints

- No JS frameworks — no React, Vue, Svelte, Angular, or similar
- No JS build step — `frontend/` files must work directly as served static assets
- File management API must whitelist the five managed directories; reject all paths outside them
- Path traversal (`..`) must be explicitly rejected with HTTP 400
- No new Python packages unless genuinely unavoidable
- All new Python routers follow existing patterns: Pydantic request/response models,
  registered exception handlers

## Performance Requirements

None beyond existing API performance.

## Security Considerations

- File management API must validate that resolved paths remain within allowed root directories
- Path traversal (`..`) must be explicitly rejected
- No auth — the deploying platform owns access control (per constitution)
- Config write endpoint can overwrite config.yaml; deployers should network-restrict if needed

## Out of Scope

- Server restart endpoint
- User authentication or session management
- JS bundler, transpiler, or build pipeline (Webpack, Vite, esbuild, etc.)
- Mobile-specific responsive design beyond Pico.css defaults
- Binary file upload or download
- goals_manifest.json editing (it is generated, not hand-edited)

## Open Questions

- None.

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- No JS frameworks (React, Vue, Svelte, Angular, or similar) in `frontend/` — all client-side logic must be plain ES6+ JavaScript with no build step
- No new Python packages in `pyproject.toml` unless the spec explicitly identifies an unavoidable gap that an existing dependency cannot fill
- All new Python routers must use Pydantic request/response models and register exception handlers consistent with the pattern in `src/corpus_council/api/app.py`
- File management API (`/files` routes) must resolve all paths and reject any request where the resolved path escapes the whitelisted root directories; `..` segments must be rejected with HTTP 400
- No hardcoded behavioral rules, personas, or domain logic in Python source — all such decisions belong in corpus/council markdown files per the constitution
- No relational database, message queue, or external service dependency introduced — flat files only (embeddings via ChromaDB remain the explicit exception)
- All LLM calls must use markdown prompt templates — no inline prompt strings in Python source
- `ruff check src/` exits 0 with no errors
- `ruff format --check src/` exits 0 with no formatting violations
- `pyright src/` exits 0 with no type errors
- Integration tests for new API endpoints must use a real temporary directory — no mocking of filesystem operations

## Dynamic Verification
- **Exercise command:** `uvicorn corpus_council.api.app:app --host 127.0.0.1 --port 8765 &; sleep 2; curl -sf http://127.0.0.1:8765/ui/index.html && curl -sf http://127.0.0.1:8765/files && kill %1`
- **Ready check:** `curl -sf http://127.0.0.1:8765/docs > /dev/null`
- **Teardown:** `kill $APP_PID`

## Execution
- **Test:** `pytest -m "not llm" tests/`
- **Typecheck:** `pyright src/`
- **Lint:** `ruff check src/ && ruff format --check src/`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `frontend/index.html`, `frontend/app.js`, and `frontend/style.css` exist and are served at `/ui`. `src/corpus_council/api/routers/files.py` and `src/corpus_council/api/routers/admin.py` exist and are registered in `app.py`. `pytest -m "not llm" tests/` exits 0. `ruff check src/` exits 0. `ruff format --check src/` exits 0. `pyright src/` exits 0.
- **Max task tries:** 3
