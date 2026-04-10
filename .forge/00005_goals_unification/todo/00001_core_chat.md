# Task 00001: Implement core/chat.py with run_goal_chat

## Role
programmer

## Objective
Create `src/corpus_council/core/chat.py` with a single public function `run_goal_chat(goal_name, user_id, conversation_id, message, config, store, llm, mode)` that loads the goal from the manifest, loads council members, retrieves corpus chunks, runs deliberation, persists the turn, and returns `(response_text, conversation_id)`.

## Context

**Task 00000 added** `goal_messages_path` and `goal_context_path` to `FileStore` in `src/corpus_council/core/store.py`. This task depends on those methods.

**Key existing files and patterns:**

`src/corpus_council/core/conversation.py` — the existing stateful conversation function. The new `run_goal_chat` follows the same pattern but:
- Accepts `goal_name` and `conversation_id` as parameters (goal-aware, keyed under goal+conversation_id)
- Uses `load_goal(goal_name, config.goals_manifest_path)` then `load_council_for_goal(goal_config, config.personas_dir)` instead of `load_council(config)`
- Raises `KeyError` if goal is not found (caller maps to 404 — `load_goal` raises `ValueError`, so catch and re-raise as `KeyError`)
- Uses `store.goal_messages_path(user_id, goal_name, conversation_id)` and `store.goal_context_path(user_id, goal_name, conversation_id)` for persistence
- Returns `tuple[str, str]` — `(final_response, conversation_id)`

**Imports needed:**
```python
from .config import AppConfig
from .consolidated import run_consolidated_deliberation
from .council import load_council_for_goal
from .deliberation import run_deliberation
from .goals import load_goal
from .llm import LLMClient
from .retrieval import ChunkResult, retrieve_chunks
from .store import FileStore
```

**`load_goal` signature** (from `src/corpus_council/core/goals.py`):
```python
def load_goal(name: str, manifest_path: Path) -> GoalConfig:
    # Raises FileNotFoundError if manifest absent
    # Raises ValueError if goal name not in manifest
```

**`load_council_for_goal` signature** (from `src/corpus_council/core/council.py`):
```python
def load_council_for_goal(goal_config: GoalConfig, personas_dir: Path) -> list[CouncilMember]:
```

**`retrieve_chunks` signature** (from `src/corpus_council/core/retrieval.py`):
```python
def retrieve_chunks(message: str, config: AppConfig) -> list[ChunkResult]:
```

**Deliberation functions:**
```python
run_deliberation(user_message, corpus_chunks, members, llm) -> DeliberationResult
run_consolidated_deliberation(user_message, corpus_chunks, members, llm) -> DeliberationResult
```

`DeliberationResult.final_response` is the string response.

**Turn record format** (follow `conversation.py` pattern):
```python
turn_record: dict[str, Any] = {
    "timestamp": datetime.now(UTC).isoformat(),
    "user_message": message,
    "deliberation_log": [...],
    "final_response": result.final_response,
}
```

**Context record format:**
```python
updated_context: dict[str, Any] = {
    "user_id": user_id,
    "goal": goal_name,
    "conversation_id": conversation_id,
    "turn_count": turn_count,
    "last_updated": datetime.now(UTC).isoformat(),
}
```

**Function signature:**
```python
def run_goal_chat(
    goal_name: str,
    user_id: str,
    conversation_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
    mode: str = "sequential",
) -> tuple[str, str]:
```

**No inline prompt strings** — all LLM templates are already markdown files in `templates/`. The existing deliberation functions reference those templates by name via `llm.call()`.

**Unit tests:** Add `tests/unit/test_chat.py` with tests that mock `LLMClient.call` to avoid real API calls. Tests must cover:
- Normal first-call flow (returns response string and conversation_id)
- Continuation call (turn_count increments, messages.jsonl grows)
- Unknown goal raises `KeyError`
- Mock pattern: subclass `LLMClient` with a `call` override (same pattern as `ConvTestLLM` in `tests/integration/test_full_conversation_flow.py`)

**Tech stack:** Python 3.12, uv.

## Steps
1. Create `src/corpus_council/core/chat.py` with `from __future__ import annotations` and full type annotations.
2. Implement `run_goal_chat`:
   - Call `load_goal(goal_name, config.goals_manifest_path)` — catch `ValueError` and re-raise as `KeyError(f"Goal not found: {goal_name!r}")`
   - Call `load_council_for_goal(goal_config, config.personas_dir)`
   - Retrieve chunks: wrap in try/except BLE001 and default to empty list on failure
   - Read context from `store.goal_context_path(user_id, goal_name, conversation_id)` — initialize if empty
   - Run deliberation based on `mode`
   - Persist turn via `store.append_jsonl(store.goal_messages_path(...))`
   - Persist updated context via `store.write_json(store.goal_context_path(...))`
   - Return `(result.final_response, conversation_id)`
3. Export `run_goal_chat` in `__all__`.
4. Create `tests/unit/test_chat.py` with unit tests using a mocked LLM subclass. The mock must call `self.render_template(template_name, context)` (real rendering) before returning fixed strings, same as existing test LLMs.
5. Run `uv run pytest tests/unit/test_chat.py` and confirm pass.
6. Run `uv run pyright src/` and confirm exit 0.
7. Run `uv run ruff check . && uv run ruff format --check .` and confirm exit 0.

## Verification
- File `src/corpus_council/core/chat.py` exists
- `src/corpus_council/core/chat.py` defines `run_goal_chat`
- `src/corpus_council/core/chat.py` contains no inline LLM prompt strings (no triple-quoted prompt blocks — verify with Grep for `llm_prompt` or similar inline content)
- `uv run pytest tests/unit/test_chat.py` exits 0
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged
- Dynamic: start, verify `run_goal_chat` import resolves, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  uv run python -c "from corpus_council.core.chat import run_goal_chat; print('OK')"
  kill $APP_PID
  ```

## Done When
- [ ] `src/corpus_council/core/chat.py` exists with fully typed `run_goal_chat`
- [ ] Unit tests pass
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/chat.py tests/unit/test_chat.py && git commit -m "task-00001: implement core chat.py with run_goal_chat"
```
