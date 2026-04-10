# Task 00009 — Full test suite green pass

## Agent
tester

## Goal
Run the complete test suite and fix any test failures introduced by the new routers,
models, or frontend files. This is a stabilization task — no new features are implemented.

## Prerequisites
- All prior tasks (00001–00008) must be complete

## Steps

### 1. Run the full test suite

```bash
pytest -m "not llm" tests/ -v 2>&1 | tail -40
```

### 2. For each failure, diagnose and fix

Common failure categories:

**A. Import errors in `models.py`**
If new models added duplicate `from typing import Literal` or `from __future__ import annotations`,
consolidate them. The file must have exactly one `from __future__ import annotations` at the top.

**B. `_MANAGED_ROOTS` not reset between tests**
If tests from `test_files_router.py` bleed state into other tests, the monkeypatch fixture
is not resetting `_MANAGED_ROOTS` correctly. Verify the fixture uses `monkeypatch.setattr`
(which resets automatically after each test).

**C. `CONFIG_PATH` not reset between tests**
Same issue as B but for `admin_module.CONFIG_PATH`. Monkeypatch handles this automatically.

**D. `StaticFiles` mount failure**
If `frontend/` does not exist, the `if _frontend_dir.is_dir()` guard in `app.py` prevents
a `RuntimeError`. If `app.py` was written without this guard, add it.

**E. `pyright` type errors from new models**
If `int | None` needs `from __future__ import annotations` to resolve, confirm that line
is present at the top of `models.py`. If using `Optional[int]` instead, that also works.

**F. Existing tests broken by new router registrations**
Confirm no existing test imported `app` and expected certain routes NOT to exist. This is
unlikely but check `test_api.py` for any negative assertions about the route list.

### 3. Run linting and type-checking

```bash
ruff check src/
ruff format --check src/
pyright src/
```

Fix any issues found. Common issues:
- Unused imports in `app.py` after adding new router imports
- Missing `__all__` exports in new router files
- `Union[X, Y]` vs `X | Y` — use `X | Y` (Python 3.10+ style, enabled by `from __future__ import annotations`)

### 4. Final verification

```bash
pytest -m "not llm" tests/ && ruff check src/ && ruff format --check src/ && pyright src/
```

All four commands must exit 0.

## Save Command

```bash
pytest -m "not llm" tests/ --tb=short -q 2>&1 | tail -10 && echo "ALL CHECKS PASSED"
```

Must print `ALL CHECKS PASSED` (indicating pytest exited 0).
