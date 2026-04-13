# Task 00004: Rename sequential → parallel in config.yaml, config.py, and chat.py

## Role
programmer

## Objective
Remove all user-facing and code-level references to `"sequential"` in `config.yaml`, `src/corpus_council/core/config.py`, and `src/corpus_council/core/chat.py`. Replace with `"parallel"`. After this task, `config.yaml` defaults to `deliberation_mode: parallel`, `AppConfig.deliberation_mode` defaults to `"parallel"`, config validation accepts `{"parallel", "consolidated"}` (not `"sequential"`), and `run_goal_chat` defaults its `mode` parameter to `"parallel"`.

## Context

**Files to change:**

**1. `config.yaml`** (project root):
Current content relevant:
```yaml
# Deliberation mode: "sequential" (default, 2N+1 LLM calls) or "consolidated" (2 LLM calls)
deliberation_mode: sequential
```
Change to:
```yaml
# Deliberation mode: "parallel" (default, N+1 LLM calls) or "consolidated" (2 LLM calls)
deliberation_mode: parallel
```

**2. `src/corpus_council/core/config.py`**:
- `AppConfig.deliberation_mode: str = "sequential"` → `"parallel"`
- `data.get("deliberation_mode", "sequential")` → `data.get("deliberation_mode", "parallel")`
- `if deliberation_mode_raw not in {"sequential", "consolidated"}:` → `{"parallel", "consolidated"}`
- Error message text: `'deliberation_mode' must be 'sequential' or 'consolidated'` → `'parallel' or 'consolidated'`

**3. `src/corpus_council/core/chat.py`**:
- `mode: str = "sequential"` in `run_goal_chat` signature → `mode: str = "parallel"`
- The `else:` branch `result = run_deliberation(message, chunks, members, llm)` remains — but the condition for it changes from checking `mode == "consolidated"` to `mode == "consolidated"` (unchanged), so `mode == "parallel"` implicitly falls to the `else` branch. No logic change needed beyond the default parameter.

**Import and export contracts:**
- `AppConfig` is imported in many places; only the default value on `deliberation_mode` changes — no structural change.
- `run_goal_chat` signature changes only the default value of `mode`.

**`test_config.py`** currently has `test_load_config_returns_all_required_fields` which calls `load_config(_REAL_CONFIG)` — after this task `config.yaml` returns `deliberation_mode: "parallel"` which must be accepted by the new validation set. No test changes needed for this.

**`test_goals_integration.py`** has a hardcoded `"deliberation_mode": "sequential"` in its `_write_config` helper. That test will fail config validation after this change. It will be fixed in task 00006 (test updates).

Tech stack: Python 3.12, YAML, mypy strict.

## Steps
1. Read `config.yaml` and update the comment and value for `deliberation_mode`.
2. Read `src/corpus_council/core/config.py` and update:
   - `AppConfig.deliberation_mode` default from `"sequential"` to `"parallel"`
   - `data.get("deliberation_mode", "sequential")` default from `"sequential"` to `"parallel"`
   - The valid-values set from `{"sequential", "consolidated"}` to `{"parallel", "consolidated"}`
   - The error message to say `'parallel' or 'consolidated'`
3. Read `src/corpus_council/core/chat.py` and update the `mode: str = "sequential"` default parameter to `mode: str = "parallel"`.
4. Run `uv run mypy src/` and fix any issues.
5. Run `uv run ruff check src/ && uv run ruff format --check src/` and fix any issues.
6. Run `uv run pytest tests/ -x -k "not llm and not goals_integration"` to check non-LLM, non-integration tests pass (some deliberation tests may still fail because they test the old sequential behavior; those will be fixed in task 00006).

## Verification
- `grep -n "sequential" src/corpus_council/core/config.py` returns no matches
- `grep -n "sequential" src/corpus_council/core/chat.py` returns no matches
- `grep -n "sequential" config.yaml` returns no matches (the comment and value are both updated)
- `grep -n "parallel" config.yaml` shows `deliberation_mode: parallel`
- `grep -n "parallel" src/corpus_council/core/config.py` shows `"parallel"` in the valid-values set and default
- `uv run mypy src/` exits 0
- `uv run ruff check src/ && uv run ruff format --check src/` exits 0
- Global Constraint — No new Python package dependencies: no changes to `pyproject.toml`
- Global Constraint — `"sequential"` absent from user-facing config: `grep -r "sequential" src/ config.yaml` returns zero matches
- Dynamic: `uv run python -c "from corpus_council.core.config import load_config; c = load_config('config.yaml'); assert c.deliberation_mode == 'parallel', c.deliberation_mode; print('OK')"` exits 0 and prints "OK"

## Done When
- [ ] `config.yaml` has `deliberation_mode: parallel`
- [ ] `AppConfig.deliberation_mode` defaults to `"parallel"`
- [ ] `load_config` accepts `"parallel"` and rejects `"sequential"` with a `ValueError`
- [ ] `run_goal_chat` defaults `mode` to `"parallel"`
- [ ] All verification checks pass

## Save Command
```
git add config.yaml src/corpus_council/core/config.py src/corpus_council/core/chat.py && git commit -m "task-00003: rename sequential to parallel in config, config.py, and chat.py"
```
