# Task 00008: Final verification — run full dynamic verification suite

## Role
product-manager

## Objective
Run the complete dynamic verification suite (ruff check, ruff format --check, mypy, pytest), confirm all deliverables from the project spec are present and correct, verify the sequential mode is unchanged, confirm no new dependencies were added to `pyproject.toml`, and confirm that `mode=invalid` returns HTTP 422. This task produces no new code — it is a validation and sign-off task.

## Context

**All prior tasks must be complete:**
- Task 00000: `AppConfig.deliberation_mode` in `config.py` and `config.yaml`
- Task 00001: `templates/council_consolidated.md` and `templates/evaluator_consolidated.md`
- Task 00002: `src/corpus_council/core/consolidated.py`
- Task 00003: `run_conversation()` and collection functions have `mode` parameter with dispatch
- Task 00004: API models have `mode` field; routers resolve and forward it
- Task 00005: CLI `--mode` flag on `chat`, `query`, `collect`
- Task 00006: `tests/unit/test_consolidated.py` with 5 unit tests
- Task 00007: `tests/integration/test_consolidated_integration.py` and updated `test_api.py`

**Full verification command list** (from `project.md` `## Dynamic Verification`):
```bash
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/corpus_council/core/
uv run pytest
```

**Deliverables checklist** (from `project.md` `## Deliverables`):
- [ ] `src/corpus_council/core/consolidated.py` exists and exports `run_consolidated_deliberation()`
- [ ] `templates/council_consolidated.md` exists
- [ ] `templates/evaluator_consolidated.md` exists
- [ ] `src/corpus_council/core/config.py` has `deliberation_mode` field in `AppConfig`
- [ ] `config.yaml` has `deliberation_mode: sequential`
- [ ] `src/corpus_council/cli/main.py` `--mode` on `chat`, `query`, `collect`
- [ ] `src/corpus_council/api/models.py` has `mode` field in `ConversationRequest`, `CollectionStartRequest`, `CollectionRespondRequest`
- [ ] `src/corpus_council/core/conversation.py` dispatches on mode
- [ ] `src/corpus_council/core/collection.py` has `mode` parameter in `start_collection` and `respond_collection`
- [ ] `tests/unit/test_consolidated.py` exists with 5 tests
- [ ] `tests/integration/test_consolidated_integration.py` exists with 3 llm-marked tests

**Sequential mode guard:** The sequential deliberation path must be unchanged. Verify:
- `run_deliberation()` in `deliberation.py` has identical signature and body to before this project
- Existing tests for deliberation, conversation, and collection all pass
- No template files for the sequential path were modified

**No new dependencies guard:** Check `pyproject.toml` — confirm no new packages were added. The consolidated mode uses only: FastAPI, Typer, Jinja2, PyYAML, anthropic SDK, ChromaDB, sentence-transformers, pydantic, pytest (all pre-existing).

**Mode resolution priority guard:** Confirm the priority order is correct in both CLI and API:
1. Per-request (`--mode` CLI flag or `mode` API field)
2. `config.yaml` `deliberation_mode`
3. Default: `"sequential"`

Verify by reading the relevant code sections.

**HTTP 422 guard:** Invalid `mode` value must return 422. This is enforced by Pydantic's `Literal` type — verify it is correctly typed in `models.py`.

## Steps

1. Run `uv run ruff check src/` — confirm exit 0. If not, list failures.

2. Run `uv run ruff format --check src/` — confirm exit 0. If not, list failures.

3. Run `uv run mypy src/corpus_council/core/` — confirm exit 0. If not, list type errors.

4. Run `uv run pytest` — confirm exit 0. Check that:
   - Coverage is >= 80% on `src/corpus_council/core/`
   - All non-llm tests pass
   - LLM-marked tests are skipped (not failed) when `ANTHROPIC_API_KEY` is absent

5. Check each deliverable file exists and contains the expected exports/signatures:
   - `src/corpus_council/core/consolidated.py` — `run_consolidated_deliberation` in `__all__`
   - `templates/council_consolidated.md` — contains Jinja2 `{% for member in members %}` loop
   - `templates/evaluator_consolidated.md` — contains `{{ council_responses }}` and `{{ escalation_summary }}`
   - `config.yaml` — contains `deliberation_mode: sequential`
   - `src/corpus_council/core/config.py` — `deliberation_mode: str = "sequential"` in `AppConfig`

6. Verify `--help` on all three CLI commands shows `--mode`:
   - `uv run corpus-council chat --help | grep --mode`
   - `uv run corpus-council query --help | grep --mode`
   - `uv run corpus-council collect --help | grep --mode`

7. Verify sequential path is unchanged:
   - `grep -n 'def run_deliberation' src/corpus_council/core/deliberation.py` shows original signature
   - `uv run pytest tests/unit/test_deliberation.py` exits 0

8. Verify no new packages in `pyproject.toml`:
   - Read `pyproject.toml` and confirm `[project.dependencies]` contains no packages that were not present before this project

9. Verify HTTP 422 for invalid mode via httpx (without running the full server):
   - Run `uv run pytest tests/integration/test_api.py -k invalid -v` and confirm the 422 test passes

10. If any check fails, report exactly which check failed and what the output was. Do not attempt to fix code — report failures and mark the task blocked.

## Verification

- All four dynamic verification commands exit 0:
  ```bash
  cd /home/buddy/projects/corpus-council
  uv run ruff check src/
  uv run ruff format --check src/
  uv run mypy src/corpus_council/core/
  uv run pytest
  ```
- All deliverables checklist items confirmed present (structural checks)
- Sequential mode tests pass: `uv run pytest tests/unit/test_deliberation.py` exits 0
- `--mode` visible in all three CLI help outputs
- HTTP 422 test passes: `uv run pytest tests/integration/test_api.py -k invalid` exits 0
- `pyproject.toml` has no new dependencies

## Done When
- [ ] `uv run ruff check src/` exits 0
- [ ] `uv run ruff format --check src/` exits 0
- [ ] `uv run mypy src/corpus_council/core/` exits 0
- [ ] `uv run pytest` exits 0 with coverage >= 80%
- [ ] All deliverable files exist with correct content
- [ ] Sequential mode tests pass unchanged
- [ ] CLI `--mode` visible on chat, query, collect
- [ ] HTTP 422 returned for invalid mode value
- [ ] No new dependencies added to `pyproject.toml`

## Save Command
```
git add -A && git commit -m "task-00008: final verification — all checks pass"
```
