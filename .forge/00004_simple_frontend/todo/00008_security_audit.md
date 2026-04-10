# Task 00008 — Security audit of path validation in `files.py` and `admin.py`

## Agent
security-engineer

## Goal
Audit the path validation implementation in `files.py` and the config write endpoint in
`admin.py`. Fix any issues found. This is a read-and-fix task — no new files are created.

## Prerequisites
- Task 00001 (`files.py`) must be complete
- Task 00002 (`admin.py`) must be complete
- Task 00005 (files router tests) must be complete

## Checks to perform

### 1. Verify `_resolve_safe_path` implements all three layers

Read `src/corpus_council/api/routers/files.py` and confirm:

**Check A — `..` rejection before resolution**
The raw `rel_path` string is checked for `..` segments BEFORE any `Path` operations:
```python
if ".." in rel_path.split("/"):
    raise HTTPException(status_code=400, detail="Path traversal not allowed")
```
If this check is missing or positioned after `Path()` construction, add it.

**Check B — root key validation**
`root_key` is verified to be in `_get_roots()` (or `_MANAGED_ROOTS`) before path resolution.
If missing, add it.

**Check C — resolved path prefix assertion**
After `(root / rel_path).resolve()`, the implementation checks:
```python
if not str(resolved).startswith(str(root)):
    raise HTTPException(status_code=400, detail="Path escapes managed root")
```
If missing or using a weaker check (e.g., `in` instead of `startswith`), fix it.

**Test**: confirm `test_path_traversal_rejected` in `test_files_router.py` would fail if
the `..` check were removed. You may verify this by temporarily removing the check and
running the test, then restoring it.

### 2. Verify `MANAGED_ROOTS` / `_MANAGED_ROOTS` uses `.resolve()`

In `_get_roots()` (or wherever `_MANAGED_ROOTS` is built), all root paths must be
`.resolve()`d:
```python
"corpus": Path(config.corpus_dir).resolve(),
```
If any path is built without `.resolve()`, fix it. This prevents symlink-based bypasses.

### 3. Verify `PUT /config` does not accept a caller-supplied path

Read `src/corpus_council/api/models.py` (or the admin router) and confirm:
- `ConfigWriteRequest` has only a `content: str` field — no `path` field.
- The `update_config` handler writes to `CONFIG_PATH` (the module-level constant), not to
  any path derived from the request body.

If a `path` field exists in `ConfigWriteRequest`, remove it.

### 4. Check for bare `except` blocks

Grep `src/corpus_council/api/routers/files.py` and `src/corpus_council/api/routers/admin.py`
for bare `except:` or `except Exception: pass` patterns. There must be none.

All exceptions must either propagate naturally (caught by FastAPI's exception handlers)
or be re-raised as `HTTPException`.

### 5. Verify `/files` root listing does not expose absolute paths

`GET /files` must return only the root key names (`["corpus", "council", ...]`), not
absolute server paths. Confirm the `FileRootsResponse` only contains `roots: list[str]`
with key names.

### 6. Run the traversal test explicitly

```bash
pytest tests/integration/test_files_router.py::test_path_traversal_rejected -v
```

If this test passes with the `..` check present, temporarily remove the check from
`_resolve_safe_path`, run the test again, confirm it fails (status code is not 400),
then restore the check. This confirms the test is actually catching the vulnerability.

**Document the result** in the task output — write a one-line comment above the `..` check
in the code:
```python
# Reject '..' segments before any Path resolution to prevent traversal attacks.
if ".." in rel_path.split("/"):
```

## Verification

```bash
ruff check src/
pyright src/
pytest tests/integration/test_files_router.py -v
```

All must exit 0.

## Save Command

```bash
ruff check src/ && pyright src/ && pytest tests/integration/test_files_router.py::test_path_traversal_rejected -v --tb=short
```

Must exit 0 and show `test_path_traversal_rejected PASSED`.
