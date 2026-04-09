# Task 00006: Write integration tests for goals pipeline and API

## Role
tester

## Objective
Create `/home/buddy/projects/corpus-council/tests/integration/test_goals_integration.py` with integration tests for the end-to-end goals CLI pipeline (marked `llm` since they require `ANTHROPIC_API_KEY`). These tests must use real goal markdown files, a real `process_goals` call to produce a manifest, and real CLI invocations via `subprocess.run` — no mocking of goal manifest loading, corpus retrieval, or council deliberation.

## Context
**Tasks 00000–00004** have implemented the full goals model: `AppConfig` with goals fields, `goals.py`, goal files, updated CLI, and updated API.

**Integration test requirements from tester.md**:
- `test_goals_process_command_exits_zero` — runs `corpus-council goals process` via `subprocess.run` against a real goals directory; asserts exit 0 and `goals_manifest.json` exists
- `test_query_with_goal_intake` — runs `corpus-council query --goal intake <message>` via `subprocess.run` against real corpus and council; asserts exit 0 and non-empty stdout
- `test_query_with_goal_create_plan` — same for `--goal create-plan`
- `test_query_with_unknown_goal_exits_nonzero` — `corpus-council query --goal nonexistent "test"`; asserts non-zero exit and stderr contains the missing goal name

**Key constraint**: All integration tests that make real LLM calls must be decorated with `@pytest.mark.llm` and must skip if `ANTHROPIC_API_KEY` is not set. Use:
```python
pytestmark = pytest.mark.llm

@pytest.fixture(autouse=True)
def require_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
```

**Test isolation**: All integration tests must work against `tmp_path`-based directories, NOT against the real project `data/`, `goals/`, or `council/` directories. Use environment variable overrides or a temporary `config.yaml` to point the CLI at `tmp_path`.

**CLI invocation strategy**: Use `subprocess.run(["corpus-council", ...], env={...}, cwd=str(tmp_path), capture_output=True, text=True)`. The environment must include `ANTHROPIC_API_KEY` and the `PATH`. Write a minimal `config.yaml` to `tmp_path` so the CLI picks it up via the default `config.yaml` path.

**Test setup**: Each test that needs a working goals pipeline must:
1. Write `tmp_path/config.yaml` pointing to `tmp_path/goals/`, `tmp_path/council/`, etc.
2. Write minimal persona files to `tmp_path/council/` (matching the persona filenames referenced in the goal files from `goals/intake.md` and `goals/create-plan.md` — Task 00002 uses `coach.md` and `analyst.md`)
3. Write goal files to `tmp_path/goals/` (copy from the real project `goals/` or write inline)
4. Run `corpus-council goals process` first to produce the manifest
5. Then run the actual assertion command

**Existing tests to NOT break**: `tests/integration/test_api.py`, `tests/integration/test_full_conversation_flow.py`, `tests/integration/test_full_collection_flow.py`, `tests/integration/test_consolidated_integration.py` may still exist. Do not modify them in this task (Task 00004 already updated `test_api.py`). If those tests reference old endpoints that no longer exist, they should have been cleaned up in Task 00004 — if not, note them as blocked.

**Subprocess config.yaml template** (write this to `tmp_path/config.yaml` in each test fixture):
```yaml
llm:
  provider: anthropic
  model: claude-haiku-4-5-20251001
embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2
data_dir: data
corpus_dir: corpus
council_dir: council
goals_dir: goals
personas_dir: council
goals_manifest_path: goals_manifest.json
templates_dir: <absolute path to real project templates/>
plans_dir: plans
chunking:
  max_size: 512
retrieval:
  top_k: 3
chroma_collection: test_corpus
deliberation_mode: sequential
```
The `templates_dir` must point to the real project's `templates/` directory (not a tmp copy) since those are real Jinja2 templates needed by the LLM client. Use `Path(__file__).parent.parent.parent / "templates"` for this path.

## Steps
1. Create `tests/integration/test_goals_integration.py`.
2. Add a `pytest.ini_options` check at the top to confirm the `llm` marker is registered (it already is in `pyproject.toml`).
3. Write a shared fixture `goals_workspace(tmp_path)` that:
   - Creates `tmp_path/goals/`, `tmp_path/council/`, `tmp_path/corpus/`, `tmp_path/data/`, `tmp_path/plans/`
   - Writes `tmp_path/council/coach.md` and `tmp_path/council/analyst.md` with valid council member front matter
   - Copies or writes `intake.md` and `create-plan.md` from the real `goals/` dir to `tmp_path/goals/`
   - Writes a minimal corpus file to `tmp_path/corpus/test.md`
   - Writes `tmp_path/config.yaml` as described above
   - Returns `tmp_path`
4. Implement the four tests described in Context above.
5. For `test_query_with_goal_intake` and `test_query_with_goal_create_plan`:
   - The test must first run `corpus-council goals process` to produce the manifest
   - Then run `corpus-council ingest corpus` (or point at tmp corpus) and `corpus-council embed` to prepare the vector store
   - Then run `corpus-council query --goal intake "What are your current goals?"` and assert exit 0 and non-empty stdout
6. Run `uv run pytest tests/integration/test_goals_integration.py -m "not llm" -v` to verify the non-LLM tests pass (if any). Run `uv run pytest -m "not llm"` for the full non-LLM suite.
7. Run `uv run ruff check . && uv run ruff format --check .` exits 0.

## Verification
- Structural: `tests/integration/test_goals_integration.py` exists
- Structural: All test functions in this file are decorated with `@pytest.mark.llm` or covered by a module-level `pytestmark`
- Structural: `ANTHROPIC_API_KEY` check is present — tests skip gracefully when the key is absent
- Structural: No `unittest.mock`, `MagicMock`, or `monkeypatch` applied to `load_goal`, `process_goals`, `run_deliberation`, or `retrieve_chunks`
- Structural: Tests use `subprocess.run` with a real `tmp_path`-based `config.yaml`, not hardcoded paths
- Behavioral: `uv run pytest tests/integration/test_goals_integration.py -m "not llm" -v` exits 0 (any non-LLM tests pass)
- Behavioral: `uv run pytest -m "not llm"` exits 0 (full non-LLM suite)
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run mypy src/` exits 0
- Constraint (no mocking of manifest loading, corpus retrieval, council deliberation): Grep `tests/integration/test_goals_integration.py` for `mock`, `patch`, `MagicMock` — must return no matches in tests exercising the goals pipeline
- Dynamic: `uv run pytest tests/integration/test_goals_integration.py -m "not llm" -v 2>&1 | tail -10` — shows collected tests and passes (or skips if API key absent, not fails)

## Done When
- [ ] `tests/integration/test_goals_integration.py` exists with four integration tests
- [ ] All tests use `tmp_path` — no writes to real project directories
- [ ] LLM tests skip gracefully when `ANTHROPIC_API_KEY` is absent
- [ ] `uv run pytest -m "not llm"` exits 0
- [ ] All verification checks pass

## Save Command
```
git add tests/integration/test_goals_integration.py && git commit -m "task-00006: add integration tests for goals CLI pipeline"
```
