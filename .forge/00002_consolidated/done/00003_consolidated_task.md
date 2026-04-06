# Task 00003: Add mode dispatch to conversation.py and collection.py

## Role
programmer

## Objective
Update `run_conversation()` in `src/corpus_council/core/conversation.py` to accept a `mode: str = "sequential"` parameter and dispatch to `run_consolidated_deliberation()` when `mode == "consolidated"`, otherwise to `run_deliberation()`. Update `start_collection()` and `respond_collection()` in `src/corpus_council/core/collection.py` to accept and thread a `mode: str = "sequential"` parameter (collection does not run deliberation, so the parameter is accepted for API/CLI symmetry but not used internally — it is a pass-through for future use). Do not modify `run_deliberation()` or any part of the sequential pipeline.

## Context

**Task 00002** created `src/corpus_council/core/consolidated.py` with `run_consolidated_deliberation()`.

**Current `run_conversation()` signature** in `src/corpus_council/core/conversation.py`:
```python
def run_conversation(
    user_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> ConversationResult:
```

The function calls `run_deliberation(message, chunks, members, llm)` at step 4. This call must be replaced with a dispatch:
```python
if mode == "consolidated":
    result = run_consolidated_deliberation(message, chunks, members, llm)
else:
    result = run_deliberation(message, chunks, members, llm)
```

Both `run_deliberation` and `run_consolidated_deliberation` return `DeliberationResult`, so downstream code is unchanged.

**Current `start_collection()` signature** in `src/corpus_council/core/collection.py`:
```python
def start_collection(
    user_id: str,
    plan_id: str,
    session_id: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> CollectionSession:
```

**Current `respond_collection()` signature**:
```python
def respond_collection(
    user_id: str,
    session_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> CollectionSession:
```

Both must gain `mode: str = "sequential"` as the last parameter (after `llm`). Since collection does not run deliberation, the `mode` parameter is accepted but not passed to any internal call — it is present for API/CLI consistency.

**Imports to add in `conversation.py`:**
```python
from .consolidated import run_consolidated_deliberation
```

This import goes alongside the existing `from .deliberation import run_deliberation`.

**Global constraints:**
- No modification to `run_deliberation()` itself or its templates
- `mode` parameter with default `"sequential"` must never raise on absent callers (backward compatible)
- All new code must pass `mypy src/corpus_council/core/` under `strict = true`
- No new Python packages

**Existing callers** (will be updated in later tasks):
- `src/corpus_council/cli/main.py` — calls `run_conversation()`, `start_collection()`, `respond_collection()` without `mode` (will be updated in Task 00005)
- `src/corpus_council/api/routers/conversation.py` — calls `run_conversation()` (will be updated in Task 00004)
- `src/corpus_council/api/routers/collection.py` — calls `start_collection()`, `respond_collection()` (will be updated in Task 00004)

Because the new `mode` parameter has a default value, all existing callers continue to work without modification until Tasks 00004 and 00005 update them.

## Steps

1. Open `src/corpus_council/core/conversation.py`. Add the import:
   ```python
   from .consolidated import run_consolidated_deliberation
   ```
   alongside the existing `from .deliberation import run_deliberation`.

2. Update the `run_conversation()` signature to:
   ```python
   def run_conversation(
       user_id: str,
       message: str,
       config: AppConfig,
       store: FileStore,
       llm: LLMClient,
       mode: str = "sequential",
   ) -> ConversationResult:
   ```

3. Replace the single `result = run_deliberation(message, chunks, members, llm)` line (step 4 in the function body) with:
   ```python
   if mode == "consolidated":
       result = run_consolidated_deliberation(message, chunks, members, llm)
   else:
       result = run_deliberation(message, chunks, members, llm)
   ```

4. Open `src/corpus_council/core/collection.py`. Update `start_collection()` signature to add `mode: str = "sequential"` after `llm`:
   ```python
   def start_collection(
       user_id: str,
       plan_id: str,
       session_id: str,
       config: AppConfig,
       store: FileStore,
       llm: LLMClient,
       mode: str = "sequential",
   ) -> CollectionSession:
   ```
   The body of `start_collection()` does not use `mode` — no other changes.

5. Update `respond_collection()` signature to add `mode: str = "sequential"` after `llm`:
   ```python
   def respond_collection(
       user_id: str,
       session_id: str,
       message: str,
       config: AppConfig,
       store: FileStore,
       llm: LLMClient,
       mode: str = "sequential",
   ) -> CollectionSession:
   ```
   The body of `respond_collection()` does not use `mode` — no other changes.

6. Update `__all__` in both files if needed (no new exports needed).

## Verification

- Structural:
  - `grep -n 'mode.*str.*sequential' /home/buddy/projects/corpus-council/src/corpus_council/core/conversation.py` shows the new parameter
  - `grep -n 'run_consolidated_deliberation' /home/buddy/projects/corpus-council/src/corpus_council/core/conversation.py` shows import and dispatch
  - `grep -n 'if mode.*consolidated' /home/buddy/projects/corpus-council/src/corpus_council/core/conversation.py` shows the dispatch branch
  - `grep -n 'mode.*str.*sequential' /home/buddy/projects/corpus-council/src/corpus_council/core/collection.py` shows two matches (start_collection and respond_collection)
  - `grep -n 'run_deliberation' /home/buddy/projects/corpus-council/src/corpus_council/core/conversation.py` still shows the original import and the `else` branch (the sequential path is not removed)
- Global constraint — sequential pipeline unchanged:
  - `grep -n 'def run_deliberation' /home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py` matches unchanged signature
  - Existing tests for `run_deliberation()` still pass: `uv run pytest tests/unit/test_deliberation.py`
- Behavioral:
  - `uv run mypy src/corpus_council/core/conversation.py` exits 0
  - `uv run mypy src/corpus_council/core/collection.py` exits 0
  - `uv run ruff check src/corpus_council/core/conversation.py src/corpus_council/core/collection.py` exits 0
  - `uv run ruff format --check src/corpus_council/core/conversation.py src/corpus_council/core/collection.py` exits 0
  - `uv run pytest tests/unit/test_conversation.py tests/unit/test_collection.py` exits 0 (existing tests pass)
- Dynamic: verify the updated signature is importable and backward-compatible:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run python -c "
  import inspect
  from corpus_council.core.conversation import run_conversation
  from corpus_council.core.collection import start_collection, respond_collection
  sig = inspect.signature(run_conversation)
  assert 'mode' in sig.parameters, 'run_conversation missing mode param'
  assert sig.parameters['mode'].default == 'sequential', 'run_conversation mode default wrong'
  sig2 = inspect.signature(start_collection)
  assert 'mode' in sig2.parameters, 'start_collection missing mode param'
  sig3 = inspect.signature(respond_collection)
  assert 'mode' in sig3.parameters, 'respond_collection missing mode param'
  print('All signatures OK')
  "
  ```

## Done When
- [ ] `run_conversation()` has `mode: str = "sequential"` parameter and dispatches to `run_consolidated_deliberation()` when `mode == "consolidated"`
- [ ] `start_collection()` and `respond_collection()` have `mode: str = "sequential"` parameter (body unchanged)
- [ ] Sequential pipeline (`run_deliberation()`) is untouched and existing tests pass
- [ ] `uv run mypy src/corpus_council/core/conversation.py` exits 0
- [ ] `uv run mypy src/corpus_council/core/collection.py` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/conversation.py src/corpus_council/core/collection.py && git commit -m "task-00003: add mode dispatch to conversation.py and collection.py"
```
