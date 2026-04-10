# Task 00000: Add FileStore goal path helpers

## Role
programmer

## Objective
Add two new methods to `FileStore` in `src/corpus_council/core/store.py`:
- `goal_messages_path(user_id: str, goal: str, conversation_id: str) -> Path` — returns `{base}/users/{shard1}/{shard2}/{user_id}/goals/{goal}/{conversation_id}/messages.jsonl` using the existing 2-level shard pattern (`user_id[0:2]` / `user_id[2:4]`)
- `goal_context_path(user_id: str, goal: str, conversation_id: str) -> Path` — returns `{base}/users/{shard1}/{shard2}/{user_id}/goals/{goal}/{conversation_id}/context.json`

No callers are written yet; this task only adds the path helper methods and their unit tests.

## Context

**File to modify:** `src/corpus_council/core/store.py`

The existing sharding pattern is defined in `user_dir`:
```python
def user_dir(self, user_id: str) -> Path:
    if len(user_id) < 4:
        raise ValueError(f"user_id must be at least 4 characters, got: {user_id!r}")
    return self.base / "users" / user_id[0:2] / user_id[2:4] / user_id
```
The new methods should call `self.user_dir(user_id)` and extend the path with `goals/{goal}/{conversation_id}/messages.jsonl` or `.../context.json`.

**Existing path helpers for reference:**
```python
def chat_messages_path(self, user_id: str) -> Path:
    return self.user_dir(user_id) / "chat" / "messages.jsonl"

def chat_context_path(self, user_id: str) -> Path:
    return self.user_dir(user_id) / "chat" / "context.json"
```
The new goal paths follow the same pattern but add `goals/{goal}/{conversation_id}/` between the user dir and the filename.

**Existing unit tests:** `tests/unit/test_store.py` — add new test cases there (do not create a new file).

**Tech stack:** Python 3.12, uv package manager.

## Steps
1. Open `src/corpus_council/core/store.py`. Below the `chat_context_path` method (line 91) and above the `collection_dir` methods, add a new section comment and two new methods:
   ```python
   # ------------------------------------------------------------------
   # Convenience path builders — goal chat
   # ------------------------------------------------------------------

   def goal_messages_path(self, user_id: str, goal: str, conversation_id: str) -> Path:
       return self.user_dir(user_id) / "goals" / goal / conversation_id / "messages.jsonl"

   def goal_context_path(self, user_id: str, goal: str, conversation_id: str) -> Path:
       return self.user_dir(user_id) / "goals" / goal / conversation_id / "context.json"
   ```
2. In `tests/unit/test_store.py`, add a new test section after the existing tests:
   - `test_goal_messages_path_correct_structure` — assert the returned path ends with `users/ab/c1/abc123ef/goals/my-goal/conv-uuid/messages.jsonl`
   - `test_goal_context_path_correct_structure` — assert the returned path ends with `users/ab/c1/abc123ef/goals/my-goal/conv-uuid/context.json`
3. Run `uv run pytest tests/unit/test_store.py` and confirm all tests pass.
4. Run `uv run pyright src/` and confirm exit 0.
5. Run `uv run ruff check . && uv run ruff format --check .` and confirm exit 0.

## Verification
- File `src/corpus_council/core/store.py` exists and defines `goal_messages_path`
- File `src/corpus_council/core/store.py` defines `goal_context_path`
- `src/corpus_council/core/store.py` exports `FileStore` (check `__all__`)
- `uv run pytest tests/unit/test_store.py` exits 0
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged (no new dependencies)
- Dynamic: start, verify `goal_messages_path` returns the expected path structure, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  uv run python -c "
  from corpus_council.core.store import FileStore
  from pathlib import Path
  s = FileStore(Path('/tmp'))
  p = s.goal_messages_path('abc123ef', 'my-goal', 'conv-uuid')
  assert str(p).endswith('users/ab/c1/abc123ef/goals/my-goal/conv-uuid/messages.jsonl'), repr(str(p))
  p2 = s.goal_context_path('abc123ef', 'my-goal', 'conv-uuid')
  assert str(p2).endswith('users/ab/c1/abc123ef/goals/my-goal/conv-uuid/context.json'), repr(str(p2))
  print('OK')
  "
  kill $APP_PID
  ```

## Done When
- [ ] `goal_messages_path` and `goal_context_path` are defined in `src/corpus_council/core/store.py`
- [ ] Unit tests for both path helpers pass
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/store.py tests/unit/test_store.py && git commit -m "task-00000: add FileStore goal path helpers"
```
