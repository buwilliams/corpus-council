# Task 00007: Update Existing Tests and Write New Parallel Deliberation Tests

## Role
tester

## Objective
Update `tests/unit/test_deliberation.py` to replace tests written for the old sequential behavior with tests that verify the new parallel behavior. Update `tests/integration/test_goals_integration.py` to replace `"sequential"` with `"parallel"` in the config fixture. Write new unit tests for `_format_chunks`, parallel execution correctness, and escalation flag detection. Write new integration tests (marked `@pytest.mark.llm`) for `POST /chat` with `mode: parallel` and the escalation path. After this task, `uv run pytest tests/` exits 0.

## Context

**Tasks completed before this one:**
- Task 00000: `LLMClient.call()` accepts `system_prompt: str | None = None`
- Task 00001: `templates/member_system.md` created; `templates/member_deliberation.md` restructured to user-turn only (`conversation_history`, `corpus_chunks`, `user_message`)
- Task 00002: `templates/final_synthesis.md` and `templates/escalation_resolution.md` use `member_responses`, `conversation_history`; persona fields removed
- Task 00003: `deliberation.py` uses `ThreadPoolExecutor`; `run_deliberation` accepts `conversation_history`, `goal_name`, `goal_description`; each member call uses `member_system.md` as system prompt; `chat.py` passes history and goal through
- Task 00004: `config.yaml` and `config.py` use `"parallel"` not `"sequential"`
- Task 00005: API `mode` field is `Literal["parallel", "consolidated"] | None`

**Current test files that must be updated:**

**`tests/unit/test_deliberation.py`** — currently tests the old sequential behavior:
- `test_deliberation_normal_path_iterates_members_descending`: asserts `deliberation_log[0].position == 3` (first log entry is position 3). Under parallel mode, all non-position-1 members run concurrently; the log order is not guaranteed to be descending. Replace this test with one that asserts all non-position-1 members appear in the log.
- `test_deliberation_escalation_triggered_skips_remaining_members`: asserts `position_2_entries == 0` (member was skipped after escalation). Under the new mode, ALL members complete regardless of escalation. Replace with a test that asserts all non-position-1 members appear in the log even when one triggers escalation.
- Other tests in the file may work as-is or need minor updates. Read the file carefully.

The `TestLLMClient` in `test_deliberation.py` intercepts `llm.call()` and returns canned responses. It will need updating for two changes:
1. **`call()` now accepts `system_prompt`** — the `TestLLMClient.call()` signature must add `system_prompt: str | None = None` to match `LLMClient.call()`. Store the `system_prompt` on `self.calls` entries so tests can assert it was set.
2. **Template context keys changed** — `"member_deliberation"` now receives `conversation_history`, `corpus_chunks`, `user_message` (not persona fields). `"final_synthesis"` now receives `conversation_history`, `user_message`, `corpus_chunks`, `member_responses`. Update any `render_template` calls in `TestLLMClient` that hardcode the old context shapes.

`TestLLMClient` should record each call as `{"template": ..., "context": ..., "system_prompt": ...}` so tests can assert on system prompt content.

**`tests/integration/test_goals_integration.py`** — the `_write_config` function has `"deliberation_mode": "sequential"`. After task 00003, `load_config` rejects `"sequential"` with `ValueError`. Change this to `"deliberation_mode": "parallel"`.

**New unit tests to add in `tests/unit/test_deliberation.py`:**
1. `test_format_chunks_empty_list` — `_format_chunks([])` returns `"No relevant corpus context available."`
2. `test_format_chunks_single_chunk` — `_format_chunks([chunk])` returns string containing source file and text
3. `test_format_chunks_multiple_chunks` — `_format_chunks([c1, c2])` returns string with separator `---` between chunks
4. `test_parallel_all_non_position1_members_called` — after `run_deliberation`, the log contains entries for all non-position-1 members
5. `test_parallel_position1_never_in_executor_phase` — only 2 `member_deliberation` calls for a 3-member council; position-1 uses `final_synthesis`
6. `test_escalation_all_members_complete_when_one_escalates` — when one member triggers escalation, all non-position-1 members still appear in the log
7. `test_escalation_uses_escalation_resolution_template` — when any member escalates, `escalation_resolution` template is used
8. `test_member_responses_in_synthesis_context` — `member_responses` key present in the `final_synthesis` call's context
9. `test_system_prompt_set_on_member_deliberation_calls` — each `member_deliberation` call in `llm.calls` has a non-empty `system_prompt`; assert the system prompt contains the member's persona text
10. `test_conversation_history_in_member_deliberation_context` — `run_deliberation` called with a non-empty `conversation_history` string; each `member_deliberation` call's context contains that history
11. `test_goal_description_in_system_prompt` — `run_deliberation` called with `goal_description="test goal description"`; each `member_deliberation` call's `system_prompt` contains `"test goal description"`

**`TestLLMClient` update needed:** The `_last_deliberating_member` tracking may still work, but the `member_deliberation` context dict no longer contains `prior_responses`. Verify the test client's `call` method doesn't break — it reads `context.get("member_name", "")` which is still present.

**New integration tests in `tests/integration/test_chat_router.py`:**
9. `test_post_chat_parallel_mode_returns_non_empty_response` — `POST /chat` with `mode: "parallel"` returns HTTP 200 and a non-empty `response` string (use the existing `ChatTestLLM` stub since this is not marked `@pytest.mark.llm`)
10. `test_post_chat_sequential_mode_returns_422` — `POST /chat` with `mode: "sequential"` returns HTTP 422 (Pydantic rejects it)

**New LLM integration tests in a new file `tests/integration/test_parallel_llm.py`:**
12. `test_parallel_deliberation_end_to_end` (marked `@pytest.mark.llm`) — calls `run_deliberation` with real `LLMClient`, passing `conversation_history="User: Hello\nAssistant: Hi"`, `goal_name="test-goal"`, `goal_description="Help the user"`. Asserts:
    - `result.final_response` is a non-empty string
    - All non-position-1 members appear in `result.deliberation_log`
    - `result.escalation_triggered` is `False`
13. `test_parallel_escalation_path_end_to_end` (marked `@pytest.mark.llm`) — configure a council member whose `escalation_rule` is guaranteed to trigger; assert `result.escalation_triggered is True` and position-1 still produces a non-empty `final_response`.

**`ChunkResult` import** for `_format_chunks` tests:
```python
from corpus_council.core.retrieval import ChunkResult
```
`ChunkResult` is a dataclass with fields: `text: str`, `source_file: str`, `chunk_index: int`, `score: float`.

**Import path for `_format_chunks`** — it is a module-level function in `deliberation.py` but not exported in `__all__`. Import directly: `from corpus_council.core.deliberation import _format_chunks` (private import for tests is acceptable).

**`conftest.py` fixtures available:**
- `test_config: AppConfig` — full config pointing to tmp_path dirs with 3 council members (synthesizer at position 1, analyst at position 2, critic at position 3) and 2 members referenced by `test-goal`
- `council_dir: Path` — 3 member files
- `templates_dir: Path` — real templates copied to tmp_path
- `file_store: FileStore`

The `test_config` fixture has `deliberation_mode` unset (no explicit value passed); `AppConfig` default is now `"parallel"` after task 00003.

Tech stack: Python 3.12, pytest, pytest-asyncio, httpx, mypy strict.

## Steps
1. Read `tests/unit/test_deliberation.py` in full.
2. Update or rewrite each test that relies on sequential ordering guarantees or escalation-breaks-chain behavior.
3. Add new unit tests 1–8 listed above.
4. Read `tests/integration/test_goals_integration.py` and change `"deliberation_mode": "sequential"` to `"deliberation_mode": "parallel"`.
5. Read `tests/integration/test_chat_router.py` and add tests 9–10.
6. Create `tests/integration/test_parallel_llm.py` with tests 11–12 marked `@pytest.mark.llm`.
7. Run `uv run pytest tests/ -x -k "not llm"` and fix any failures.
8. Run `uv run mypy src/` — confirm exits 0 (test files are not mypy-checked per `pyproject.toml` `[tool.mypy]` pointing only at `src/`).
9. Run `uv run ruff check src/ && uv run ruff format --check src/` — exits 0.

## Verification
- `uv run pytest tests/ -x -k "not llm"` exits 0
- `grep -rn "sequential" tests/` returns no matches (all `"sequential"` references in tests are gone)
- `grep -n "test_parallel" tests/unit/test_deliberation.py` returns at least 2 matches (new parallel tests)
- `grep -n "test_post_chat_sequential_mode_returns_422" tests/integration/test_chat_router.py` returns a match
- File `tests/integration/test_parallel_llm.py` exists
- `grep -n "pytest.mark.llm" tests/integration/test_parallel_llm.py` returns at least 2 matches
- `uv run mypy src/` exits 0
- `uv run ruff check src/ && uv run ruff format --check src/` exits 0
- Global Constraint — No LLM calls mocked in integration tests: `grep -n "monkeypatch\|mock\|Mock\|patch" tests/integration/test_parallel_llm.py` returns no matches that mock LLM calls (the file must use real `LLMClient`)
- Global Constraint — `"sequential"` absent: `grep -r "sequential" tests/` returns no matches
- Dynamic: `uv run pytest tests/ -m llm -x` exits 0 (real LLM calls — requires `ANTHROPIC_API_KEY` set in environment)

## Done When
- [ ] All existing non-LLM tests pass: `uv run pytest tests/ -x -k "not llm"` exits 0
- [ ] `tests/integration/test_parallel_llm.py` exists with 2 `@pytest.mark.llm` tests
- [ ] `"sequential"` does not appear in any test file
- [ ] All verification checks pass

## Save Command
```
git add tests/ && git commit -m "task-00007: update tests for parallel mode, system prompt split, conversation history, and goal threading"
```
