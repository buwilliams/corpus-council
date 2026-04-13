# Task 00002: Update FileStore to Accept users_dir as Base

## Role
data-engineer

## Objective
Refactor `src/corpus_council/core/store.py` so that `FileStore` is initialized with the `users_dir` path (`data_dir / "users"`) rather than `data_dir`. Remove the hardcoded `/ "users"` prefix from `user_dir()` and all path builder methods, since the base is now already the users root. Update every callsite that constructs `FileStore(config.data_dir)` to use `FileStore(config.users_dir)` instead.

## Context
**Why this change is needed**: The project spec defines `users_dir` as `data_dir / "users"` and requires `FileStore` to be initialized with `config.users_dir`. Currently `FileStore.__init__` takes `base: Path` and `user_dir()` returns `self.base / "users" / shard1 / shard2 / user_id`. If we change init to take `users_dir` (i.e., `data_dir / "users"`), then `user_dir()` must return `self.base / shard1 / shard2 / user_id` (dropping the redundant `"users"` prefix) so the actual files land at `data_dir/users/ab/c1/userid/` — identical behavior, different init contract.

**File to modify**: `/home/buddy/projects/corpus-council/src/corpus_council/core/store.py`

**Current `user_dir` implementation**:
```python
def user_dir(self, user_id: str) -> Path:
    if len(user_id) < 4:
        raise ValueError(f"user_id must be at least 4 characters, got: {user_id!r}")
    return self.base / "users" / user_id[0:2] / user_id[2:4] / user_id
```

**Target `user_dir` implementation** (after this task):
```python
def user_dir(self, user_id: str) -> Path:
    if len(user_id) < 4:
        raise ValueError(f"user_id must be at least 4 characters, got: {user_id!r}")
    return self.base / user_id[0:2] / user_id[2:4] / user_id
```

`self.base` is now `data_dir / "users"`, so the resolved path is still `data_dir/users/ab/c1/userid/` — no functional change.

**Callsites to update** — all places that construct `FileStore(config.data_dir)` must become `FileStore(config.users_dir)`:

1. `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` — `store = FileStore(config.data_dir)` in the `chat` command (line ~92).
2. `/home/buddy/projects/corpus-council/src/corpus_council/api/app.py` — wherever the global `store` is initialized.
3. `/home/buddy/projects/corpus-council/tests/conftest.py` — `file_store` fixture: `return FileStore(test_config.data_dir)` must become `FileStore(test_config.users_dir)`.
4. `/home/buddy/projects/corpus-council/tests/integration/test_chat_router.py` and `test_admin_router.py` — fixtures that set `app_module.store = FileStore(test_config.data_dir)` must use `test_config.users_dir`.

**AppConfig availability**: Task 00001 added `users_dir` as a `@property` to `AppConfig` returning `data_dir / "users"`. This task depends on Task 00001 being complete.

**Tech stack**: Python 3.12, mypy strict, ruff.

**Existing test `test_user_dir_correct_sharding`** in `tests/unit/test_store.py` currently asserts:
```python
assert result == tmp_path / "users" / "ab" / "c1" / "abc123ef"
```
After this change, `FileStore(tmp_path).user_dir("abc123ef")` returns `tmp_path / "ab" / "c1" / "abc123ef"`. But if the test is updated to use `FileStore(tmp_path / "users")`, the result is `tmp_path / "users" / "ab" / "c1" / "abc123ef"` — same absolute path. Update the test fixture call: `store = FileStore(tmp_path / "users")`.

Similarly, `test_goal_messages_path_correct_structure` and `test_goal_context_path_correct_structure` assert paths ending with `"users/ab/c1/abc123ef/goals/..."`. Initialize those stores with `tmp_path / "users"` and the assertions still hold.

All other store tests (`append_jsonl`, `write_json`, etc.) use `FileStore(tmp_path)` for non-user-sharded operations and are unaffected — those tests never call `user_dir()`.

## Steps
1. Read `/home/buddy/projects/corpus-council/src/corpus_council/core/store.py` in full.
2. Update `FileStore.user_dir()`: remove `/ "users"` from the return value. Update the docstring to note that `base` is the users root (i.e., `data_dir/users/`).
3. Update the class docstring to say the base is the users root, and the sharding is `{base}/{user_id[0:2]}/{user_id[2:4]}/{user_id}/`.
4. Read `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py`. Change `FileStore(config.data_dir)` to `FileStore(config.users_dir)`.
5. Read `/home/buddy/projects/corpus-council/src/corpus_council/api/app.py`. Change `FileStore(config.data_dir)` to `FileStore(config.users_dir)`.
6. Read `/home/buddy/projects/corpus-council/tests/conftest.py`. In the `file_store` fixture, change `FileStore(test_config.data_dir)` to `FileStore(test_config.users_dir)`. Also update any integration test fixtures that initialize `app_module.store = FileStore(test_config.data_dir)` to use `test_config.users_dir`.
7. Read `/home/buddy/projects/corpus-council/tests/unit/test_store.py`. Update `test_user_dir_correct_sharding`, `test_goal_messages_path_correct_structure`, and `test_goal_context_path_correct_structure` to initialize `FileStore(tmp_path / "users")` so the expected path assertions remain correct.
8. Run quality checks.

## Verification
- Structural: `grep -n "FileStore(config.data_dir)\|FileStore(test_config.data_dir)" /home/buddy/projects/corpus-council/src/ /home/buddy/projects/corpus-council/tests/` returns no matches (all uses are now `users_dir`).
- Structural: `grep -n '"users"' /home/buddy/projects/corpus-council/src/corpus_council/core/store.py` returns no matches inside `user_dir()` — the `"users"` literal is removed from that method.
- Behavioral: `uv run ruff check src/` exits 0.
- Behavioral: `uv run mypy src/` exits 0.
- Behavioral: `uv run pytest tests/unit/test_store.py` exits 0 with all store tests passing.
- Global Constraint: No new packages in `pyproject.toml`.
- Dynamic: `python -c "
from pathlib import Path
import tempfile, os
with tempfile.TemporaryDirectory() as d:
    from corpus_council.core.store import FileStore
    users_dir = Path(d) / 'users'
    store = FileStore(users_dir)
    p = store.user_dir('abc123ef')
    expected = users_dir / 'ab' / 'c1' / 'abc123ef'
    assert p == expected, f'{p!r} != {expected!r}'
    print('OK')
"` prints `OK`.

## Done When
- [ ] `FileStore.user_dir()` does not contain `/ "users"` in its return value.
- [ ] All callsites that constructed `FileStore(config.data_dir)` now use `FileStore(config.users_dir)`.
- [ ] `tests/unit/test_store.py` store path tests initialize with `tmp_path / "users"` and pass.
- [ ] `uv run ruff check src/` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run pytest tests/unit/test_store.py` exits 0.

## Save Command
```
git add src/corpus_council/core/store.py src/corpus_council/cli/main.py src/corpus_council/api/app.py tests/conftest.py tests/unit/test_store.py tests/integration/test_chat_router.py tests/integration/test_admin_router.py && git commit -m "task-00002: update FileStore to use users_dir as base, remove hardcoded users/ prefix"
```
