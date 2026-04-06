# Task 00007: Write integration tests for the consolidated path

## Role
tester

## Objective
Create `tests/integration/test_consolidated_integration.py` with three integration tests that exercise the full consolidated path against real LLM calls. All three tests are marked `@pytest.mark.llm` and skipped unless `ANTHROPIC_API_KEY` is set. Also update `tests/integration/test_api.py` to add two new test cases: `POST /conversation` with `"mode": "consolidated"` returns 200, and `POST /conversation` with `"mode": "invalid"` returns 422. The API test cases do NOT require a real LLM (they can use the existing httpx-based test client setup).

## Context

**Tasks completed before this task:**
- Task 00000: `AppConfig.deliberation_mode` exists
- Task 00001: Both consolidated templates exist
- Task 00002: `run_consolidated_deliberation()` exists
- Task 00003: `run_conversation()` dispatches on `mode`
- Task 00004: API models have `mode` field; routers resolve and forward it
- Task 00005: CLI `--mode` flag on all three commands
- Task 00006: Unit tests for `consolidated.py` pass

**Existing test infrastructure:**

`tests/conftest.py` provides:
- `test_config: AppConfig` — all paths in `tmp_path`, no real API calls possible unless `ANTHROPIC_API_KEY` set
- `file_store: FileStore`
- `corpus_dir`, `council_dir`, `templates_dir`, `plans_dir`, `data_dir` fixtures
- The `council_dir` fixture has 3 members: "Final Synthesizer" (pos 1), "Domain Analyst" (pos 2), "Adversarial Critic" (pos 3)

**Existing `tests/integration/test_api.py`:** Already has tests for all 6 endpoints using `httpx.AsyncClient(app=app, base_url="http://test")`. Study its imports and structure to add new test cases consistently.

Read `tests/integration/test_api.py` before writing — add the new test cases to this file rather than creating a new file.

**Key imports for integration tests:**
```python
import os
import subprocess
import pytest
from corpus_council.core.conversation import run_conversation
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
```

**`llm` marker setup:** In `pyproject.toml`, check if `pytest.mark.llm` is registered. If not, add it to `[tool.pytest.ini_options]` markers list. Tests with `@pytest.mark.llm` must include:
```python
if not os.environ.get("ANTHROPIC_API_KEY"):
    pytest.skip("ANTHROPIC_API_KEY not set")
```
at the start of the test function (or use a `pytestmark` at module level with a fixture that auto-skips).

**Integration test 1: `test_run_conversation_consolidated_mode`**
- Ingest the real corpus from `corpus_dir` into ChromaDB in `tmp_path`
- Embed the corpus
- Instantiate `LLMClient(test_config)` with real API key
- Call `run_conversation("testuser", "What are the key advances in AI?", test_config, file_store, llm, mode="consolidated")`
- Assert returns `ConversationResult` with `result.response` non-empty (len > 0)
- Assert `result.turn_count == 1`
- Assert `messages.jsonl` was written to the data directory

**Integration test 2: `test_post_conversation_consolidated_via_api`**
- Use `httpx.AsyncClient(app=app, base_url="http://test")`
- POST `{"user_id": "apitest", "message": "What is AI?", "mode": "consolidated"}` to `/conversation`
- Assert HTTP 200
- Assert response JSON has non-empty `"response"` field

**Integration test 3: `test_query_command_consolidated_mode`**
- Run `uv run corpus-council query testcliuser "What is AI?" --mode consolidated` via `subprocess.run(..., capture_output=True, text=True)`
- Assert `result.returncode == 0`
- Assert `result.stdout.strip()` is non-empty

**API test additions (non-llm, in `test_api.py`):**

Two new test cases to add to the existing `test_api.py`:
```python
async def test_post_conversation_mode_consolidated_returns_200(...):
    # POST with mode=consolidated — must return 200 with response field (uses monkeypatched LLM)
    
async def test_post_conversation_mode_invalid_returns_422(...):
    # POST with mode=invalid_mode — must return 422
```

The `mode=invalid_mode` test does NOT require a real LLM — Pydantic rejects it before any handler logic runs.

For the `mode=consolidated` test in `test_api.py`, check how the existing `test_api.py` handles LLM calls (likely monkeypatched). Follow the same pattern.

**Coverage threshold:** `pytest` is configured with `--cov-fail-under=80` on `src/corpus_council/core/`. Adding tests for the consolidated path must bring or keep coverage above 80%.

**Global constraints:**
- No mocking of: corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB, prompt template rendering
- `llm` marker tests skip without `ANTHROPIC_API_KEY`
- Non-llm API tests follow existing `test_api.py` patterns

## Steps

1. Read `tests/integration/test_api.py` in full to understand existing test structure, fixtures, and how the FastAPI test client is set up.

2. Add two new test cases to `tests/integration/test_api.py`:
   - `test_post_conversation_mode_invalid_returns_422`: POST with `"mode": "invalid_mode"`, assert HTTP 422
   - `test_post_conversation_mode_consolidated_returns_200`: POST with `"mode": "consolidated"`, assert HTTP 200 and `"response"` key in JSON body (follow existing pattern for LLM stubbing)

3. Create `tests/integration/test_consolidated_integration.py`:
   - Add module-level `pytestmark = pytest.mark.llm` or per-test skip check
   - Import required modules
   - Implement `test_run_conversation_consolidated_mode`: real corpus ingestion, embedding, `run_conversation(..., mode="consolidated")`, assert non-empty response
   - Implement `test_post_conversation_consolidated_via_api`: httpx client POST with `"mode": "consolidated"`, assert 200 and non-empty response
   - Implement `test_query_command_consolidated_mode`: subprocess run of CLI with `--mode consolidated`, assert exit 0 and non-empty stdout

4. Check `pyproject.toml` for pytest marker registration. If `llm` marker is not registered, add it:
   ```toml
   [tool.pytest.ini_options]
   markers = [
       "llm: tests that require a real LLM API key (ANTHROPIC_API_KEY)",
   ]
   ```

5. Run `uv run pytest tests/unit/ tests/integration/test_api.py -v` (non-llm tests) and verify all pass.

## Verification

- Structural:
  - File `tests/integration/test_consolidated_integration.py` exists
  - `grep -n 'def test_' /home/buddy/projects/corpus-council/tests/integration/test_consolidated_integration.py` shows 3 test functions
  - `grep -n 'mark.llm\|ANTHROPIC_API_KEY' /home/buddy/projects/corpus-council/tests/integration/test_consolidated_integration.py` shows llm marker usage
  - `grep -n 'test_post_conversation_mode_invalid\|test_post_conversation_mode_consolidated' /home/buddy/projects/corpus-council/tests/integration/test_api.py` shows 2 new test functions
- Global constraints:
  - No mocking of template rendering, FileStore, ChromaDB, or corpus loading in integration test file
  - `grep -n 'mock\|Mock\|patch' /home/buddy/projects/corpus-council/tests/integration/test_consolidated_integration.py` returns no forbidden mocks (only acceptable: monkeypatching LLM HTTP transport in non-llm tests)
- Behavioral:
  - `uv run pytest tests/unit/ tests/integration/test_api.py -v` exits 0 (all non-llm tests pass)
  - `uv run ruff check tests/integration/test_consolidated_integration.py tests/integration/test_api.py` exits 0
  - `uv run ruff format --check tests/integration/test_consolidated_integration.py tests/integration/test_api.py` exits 0
- Dynamic: run non-llm tests and verify 422 case passes:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run pytest tests/integration/test_api.py -v -k "invalid" 2>&1 | tail -10
  ```
  Output must show the invalid-mode test passed.

## Done When
- [ ] `tests/integration/test_consolidated_integration.py` has 3 tests, all marked `llm`
- [ ] `tests/integration/test_api.py` has 2 new test cases (invalid mode returns 422, consolidated mode returns 200)
- [ ] `uv run pytest tests/unit/ tests/integration/test_api.py` exits 0 (non-llm tests pass)
- [ ] No mocking of template rendering, FileStore, ChromaDB in integration tests
- [ ] `uv run ruff check tests/integration/test_consolidated_integration.py tests/integration/test_api.py` exits 0
- [ ] All verification checks pass

## Save Command
```
git add tests/integration/test_consolidated_integration.py tests/integration/test_api.py && git commit -m "task-00007: add integration tests for consolidated path"
```
