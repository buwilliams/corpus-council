# Plan: Simple Frontend (00004)

## Summary

Ten tasks deliver the complete Simple Frontend feature: two new FastAPI routers
(`files.py`, `admin.py`), router registration + StaticFiles mount in `app.py`, three
static frontend files, three new integration test files, a security audit pass, a test
suite stabilization pass, and a final product validation sweep.

## Task Sequence

| # | File | Agent | What it does | Depends on |
|---|------|-------|--------------|------------|
| 00001 | `todo/00001_files_router.md` | programmer | Create `src/corpus_council/api/routers/files.py` and add file-management Pydantic models to `models.py` | — |
| 00002 | `todo/00002_admin_router.md` | programmer | Create `src/corpus_council/api/routers/admin.py` and add admin Pydantic models to `models.py` | 00001 |
| 00003 | `todo/00003_register_routers_and_static.md` | programmer | Register all four new routers + StaticFiles mount in `app.py` | 00001, 00002 |
| 00004 | `todo/00004_frontend_files.md` | programmer | Create `frontend/index.html`, `frontend/app.js`, `frontend/style.css` | 00003 |
| 00005 | `todo/00005_test_files_router.md` | tester | Write `tests/integration/test_files_router.py` (13 tests) | 00001, 00003 |
| 00006 | `todo/00006_test_admin_router.md` | tester | Write `tests/integration/test_admin_router.py` (9 tests) | 00002, 00003 |
| 00007 | `todo/00007_test_router_registration.md` | tester | Write `tests/integration/test_router_registration.py` (6 tests) | 00003 |
| 00008 | `todo/00008_security_audit.md` | security-engineer | Audit and fix path validation in `files.py` and `admin.py` | 00005 |
| 00009 | `todo/00009_full_test_suite.md` | tester | Run full test suite, fix failures, ensure ruff+pyright pass | 00004–00008 |
| 00010 | `todo/00010_product_validation.md` | product-manager | Trace every spec deliverable to a concrete artifact | 00009 |

## Key Design Decisions

### `_MANAGED_ROOTS` lazy population
`files.py` builds the root path map lazily inside `_get_roots()` rather than at module
load time, to avoid the circular import that would occur if `config` were accessed before
`app.py` finishes initializing. Integration tests patch `_MANAGED_ROOTS` directly via
`monkeypatch.setattr(files_module, "_MANAGED_ROOTS", resolved)`.

### AppConfig field names
The five managed directories map to these `AppConfig` fields (confirmed from `config.py`):
- `corpus` → `config.corpus_dir`
- `council` → `config.council_dir`
- `plans` → `config.plans_dir`
- `goals` → `config.goals_dir`
- `templates` → `config.templates_dir`

### `CONFIG_PATH` module-level variable
`admin.py` exposes `CONFIG_PATH: Path = Path("config.yaml")` at module level so integration
tests can patch it without touching the filesystem at the real config path.

### `StaticFiles` mount guard
`app.py` mounts `frontend/` only if the directory exists (`if _frontend_dir.is_dir()`),
preventing a `RuntimeError` when tests run before task 00004 completes.

### `process_goals` mock in admin tests
`POST /admin/goals/process` calls `process_goals()` which validates persona files (an
LLM-adjacent operation). Integration tests mock `corpus_council.core.goals.process_goals`
at the module level (not the router level) because the router does a local import inside
the handler.

## Completion Condition
- All ten tasks in `done/`
- `frontend/index.html`, `frontend/app.js`, `frontend/style.css` exist
- `src/corpus_council/api/routers/files.py` and `admin.py` exist and are registered
- `conversation.router` and `collection.router` registered in `app.py`
- `pytest -m "not llm" tests/` exits 0
- `ruff check src/` exits 0
- `ruff format --check src/` exits 0
- `pyright src/` exits 0
