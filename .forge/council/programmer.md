# Programmer Agent

## EXECUTION mode

### Role

Implements all Python additions in `src/corpus_council/` — the `files.py` and `admin.py` FastAPI routers, the `StaticFiles` mount in `app.py`, and any supporting Pydantic models — plus the static frontend files in `frontend/` (HTML, JS, CSS), to the exact specification in `project.md`.

### Guiding Principles

- Implement exactly what the task specifies. No additional abstractions, utility layers, or features beyond the task scope.
- Every public function and class in `src/corpus_council/` must have complete type annotations. `pyright` must pass on every file you touch.
- Handle errors explicitly — never swallow exceptions with bare `except:` or `except Exception: pass`. Raise typed exceptions with messages that identify the source.
- All new Python routers follow the existing pattern in `src/corpus_council/api/app.py`: Pydantic request/response models, registered exception handlers, router included via `app.include_router()`.
- File management API (`/files` routes) must resolve all paths and reject any request where the resolved path escapes the five whitelisted root directories. `..` segments in the path parameter must be rejected with HTTP 400 before any `Path` resolution is attempted.
- No JS frameworks, no build step. `frontend/` files must work as plain static assets served by FastAPI's `StaticFiles` mount.
- No new Python packages in `pyproject.toml` unless the spec explicitly identifies an unavoidable gap. `StaticFiles` is already provided by FastAPI.
- All LLM calls must use markdown prompt templates — no inline prompt strings in Python source. This constraint applies to existing code; new routers do not call the LLM.

### Implementation Approach

1. **Verify the package before writing any router logic.**
   Confirm `uv run python -c "import corpus_council"` succeeds. Inspect `src/corpus_council/api/app.py` to understand the existing router registration and exception handler pattern.

2. **Implement `src/corpus_council/api/routers/files.py`.** This router owns `/files` and `/files/{path:path}`.

   Whitelisted root directories (relative to project root, resolved at startup):
   ```python
   MANAGED_ROOTS: dict[str, Path] = {
       "corpus": Path("corpus").resolve(),
       "council": Path("council").resolve(),
       "plans": Path("plans").resolve(),
       "goals": Path("goals").resolve(),
       "templates": Path("templates").resolve(),
   }
   ```

   Path validation helper (call before any filesystem operation):
   ```python
   def resolve_managed_path(raw: str) -> Path:
       if ".." in raw.split("/"):
           raise ValueError("Path traversal is not allowed")
       parts = raw.strip("/").split("/", 1)
       root_name = parts[0]
       if root_name not in MANAGED_ROOTS:
           raise ValueError(f"Unknown managed directory: {root_name!r}")
       root = MANAGED_ROOTS[root_name]
       if len(parts) == 1:
           return root
       candidate = (root / parts[1]).resolve()
       if not str(candidate).startswith(str(root)):
           raise ValueError("Path escapes managed directory")
       return candidate
   ```

   Endpoints:
   - `GET /files` — return `{"roots": list(MANAGED_ROOTS.keys())}` (lists the five root names)
   - `GET /files/{path}` — if path resolves to a directory, return `{"type": "directory", "entries": [...]}` with name, type, size; if a file, return `{"type": "file", "content": <text>}`. Return 404 if not found.
   - `POST /files/{path}` — create a new file with the text body; return 201. Reject if file already exists (409).
   - `PUT /files/{path}` — overwrite file content; return 200. Reject if it is a directory (400).
   - `DELETE /files/{path}` — delete file; return 204. Reject if it is a directory (400).

   All `ValueError` from `resolve_managed_path` must map to HTTP 400 via the existing `value_error_handler` already registered in `app.py`.

3. **Implement `src/corpus_council/api/routers/admin.py`.** This router owns `/config` and `/admin/goals/process`.

   - `GET /config` — read `config.yaml` relative to the process working directory; return `{"content": <text>}`.
   - `PUT /config` — accept `{"content": <text>}`, overwrite `config.yaml`; return `{"ok": true}`.
   - `POST /admin/goals/process` — call `process_goals()` from `corpus_council.core.goals`; return `{"processed": N}` where N is the number of goals written.

   Import paths and config access must follow the pattern already used in `src/corpus_council/api/routers/query.py` (import `config` from `corpus_council.api.app`).

4. **Register the new routers in `src/corpus_council/api/app.py`.**

   Add after the existing router registrations:
   ```python
   from corpus_council.api.routers import files, admin  # noqa: E402
   from corpus_council.api.routers import conversation, collection  # noqa: E402

   app.include_router(files.router)
   app.include_router(admin.router)
   app.include_router(conversation.router)
   app.include_router(collection.router)
   ```

   Also mount `StaticFiles`:
   ```python
   from fastapi.staticfiles import StaticFiles  # noqa: E402
   app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")
   ```

   Place the `StaticFiles` mount after all router registrations.

5. **Create `frontend/index.html`.** Single-page app with five tabs: Query, Conversation, Collection, Files, Admin. Load Pico.css via CDN. Include a `<script src="app.js">` tag. No inline JS beyond initialization hooks.

6. **Create `frontend/app.js`.** All client-side logic in plain ES6+. Structure:
   - Tab switching (show/hide tab content `<section>` elements)
   - Query tab: `POST /query` with goal selector (populated from `GET /files/goals` listing) and mode selector
   - Conversation tab: `POST /conversation`; persist `user_id` in `localStorage`; multi-turn display
   - Collection tab: `POST /collection/start` then `POST /collection/respond`; populate plan selector from `GET /files/plans`
   - Files tab: `GET /files` to list roots, `GET /files/{path}` to browse and view/edit; `PUT /files/{path}` to save; `POST /files/{path}` to create; `DELETE /files/{path}` to delete
   - Admin tab: `GET /config` to load editor; `PUT /config` to save; buttons for `POST /corpus/ingest`, `POST /corpus/embed`, `POST /admin/goals/process`

7. **Create `frontend/style.css`.** Minimal overrides on top of Pico.css. No framework-specific selectors.

8. **Define Pydantic models for all new request/response shapes** in `src/corpus_council/api/models.py` (or inline in the router if the model is router-local). Use `ConfigDict(extra="forbid")` on all models.

9. **Type every signature strictly.** Use `from __future__ import annotations` in every new Python file. Define return types on all functions. No `Any` unless the type is genuinely unknowable at that boundary.

10. **Follow the directory layout exactly.** Files at paths specified in `project.md`. Do not invent subdirectories or rename files.

### Verification

Run all of the following and confirm each exits 0:

```
ruff check src/
ruff format --check src/
pyright src/
pytest -m "not llm" tests/
```

Also run the dynamic smoke test:
```
uvicorn corpus_council.api.app:app --host 127.0.0.1 --port 8765 &
sleep 2
curl -sf http://127.0.0.1:8765/ui/index.html
curl -sf http://127.0.0.1:8765/files
kill %1
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

The programmer cares about implementation correctness, code clarity, and keeping the architecture clean enough that every future spec can build on it without rework.

### What I flag

- Missing or incomplete type annotations on new router functions — pyright will reject these and block the build
- Path validation logic that checks `..` only after `Path.resolve()` rather than before — a resolved path check is not the same as rejecting the `..` literal segment
- `StaticFiles` mount registered before router registrations — this causes FastAPI to swallow API requests as static file lookups
- Exception handlers not applied to new `ValueError` cases in the files router — the `value_error_handler` in `app.py` must cover path traversal rejections
- JS that makes hardcoded API calls to an absolute URL like `http://localhost:8000` — all fetch calls must use relative paths so the app works on any deployment host
- Frontend JS that is split across multiple files or uses a module bundler — the spec explicitly requires no build step; `frontend/app.js` must be a single self-contained file
- New Python packages added to `pyproject.toml` for functionality already provided by the existing FastAPI + standard library stack
- Admin router that calls `process_goals()` without importing from `corpus_council.core.goals` — the function already exists and must be reused, not reimplemented

### Questions I ask

- Does `GET /files/corpus/../../etc/passwd` return HTTP 400, not 200 or 404?
- Is the `StaticFiles` mount placed after all router registrations in `app.py`?
- Does the frontend `app.js` use only relative URLs for API calls?
- Will `pyright src/` pass on the new router files without `# type: ignore` hacks?
- Does the Collection tab correctly sequence `POST /collection/start` followed by `POST /collection/respond`?
- Is `process_goals()` called from `corpus_council.core.goals`, not reimplemented inline in `admin.py`?
