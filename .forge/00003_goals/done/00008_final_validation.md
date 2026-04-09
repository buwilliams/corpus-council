# Task 00008: Final validation — verify all deliverables from project.md

## Role
product-manager

## Objective
Perform a complete end-to-end validation of every deliverable listed in `project.md`. This task does not write new code — it runs verification commands, reads output files, and confirms that the goals model is fully implemented as specified. If any deliverable is incomplete, broken, or missing, the agent must emit `<task-blocked>` with a precise description of what is wrong, what was expected, and what was found.

## Context
All previous tasks (00000–00007) should be complete. This task reviews their combined output.

**Deliverables from project.md to verify**:
1. Goal file format: a documented markdown schema (in `docs/goal-authoring-guide.md` and `goals.py` docstring)
2. `corpus-council goals process` CLI command that validates and registers goal files
3. `goals_manifest.json` produced by the process step, listing all registered goals
4. Updated query CLI and API to accept `--goal <name>`
5. `goals/intake.md` — goal file for structured intake interview
6. `goals/create-plan.md` — goal file for COM-B 6-week plan synthesis
7. Removal of hardcoded collection/conversation mode distinction from core orchestration
8. Documentation update: goal authoring guide

**Global Constraints to verify**:
- No hardcoded behavioral rules, council selection logic, or corpus scoping in Python source
- No new external Python packages in `pyproject.toml`
- Goal files are markdown (`.md`) only
- Goal manifest loading, corpus retrieval, and council deliberation are never mocked in tests
- `ruff check .` exits 0
- `ruff format --check .` exits 0
- `mypy` exits 0 under strict mode
- Persona path traversal validated to stay within personas directory
- `--mode consolidated|sequential` flag continues to work
- No secrets in source

## Steps
1. **Verify goal file format documentation**:
   - Read `docs/goal-authoring-guide.md` — confirm it exists and contains sections for file format, authority tiers, corpus path, process command, runtime usage, path safety, and a worked example
   - Run `uv run python -c "import corpus_council.core.goals; print(corpus_council.core.goals.__doc__[:100])"` — confirm non-empty docstring

2. **Verify `corpus-council goals process`**:
   - Create minimal test persona files: `echo "---\nname: Coach\npersona: A coach\nprimary_lens: coaching\nposition: 1\nrole_type: synthesizer\nescalation_rule: Halt\n---\nbody" > /tmp/test_council/coach.md` (or equivalent)
   - Run `corpus-council goals process` with the real project config pointing at `goals/intake.md` and `goals/create-plan.md` — if `council/coach.md` and `council/analyst.md` do not exist, create minimal stubs
   - Confirm exit code 0
   - Confirm `goals_manifest.json` exists at the configured path
   - Run `corpus-council goals process` again — confirm exit code 0 and manifest is byte-for-byte identical to the first run

3. **Verify `goals_manifest.json` structure**:
   - Parse the manifest JSON
   - Confirm it is a list containing at least two entries: `intake` and `create-plan`
   - Confirm each entry has `name`, `desired_outcome`, `council`, and `corpus_path` fields
   - Confirm `council` is a list with at least one entry per goal, each with `persona_file` and `authority_tier`

4. **Verify updated query CLI**:
   - Run `corpus-council query --help` — confirm `--goal` and `--mode` flags are listed
   - Run `corpus-council query --goal nonexistent "test"` — confirm non-zero exit and stderr/stdout contains the missing goal name
   - If `ANTHROPIC_API_KEY` is set: run `corpus-council query --goal intake "test" --mode sequential` and `--mode consolidated` — confirm exit 0 and non-empty output for both

5. **Verify `goals/intake.md` and `goals/create-plan.md`**:
   - Confirm both files exist and are valid YAML front matter
   - Confirm both contain `desired_outcome`, `corpus_path`, and `council` with `persona_file` and `authority_tier`
   - Confirm both reference the same persona filenames

6. **Verify removal of hardcoded collection/conversation dispatch**:
   - Grep `src/corpus_council/` for routing dispatch on literal strings `"collection"` or `"conversation"` in the query command, API query endpoint, and any core orchestration:
     ```bash
     grep -r '"collection"\|"conversation"' src/corpus_council/cli/main.py src/corpus_council/api/routers/ || echo "CLEAN"
     ```
   - Confirm the query command in `main.py` does not dispatch on these strings
   - Confirm `src/corpus_council/api/app.py` does not include conversation or collection routers

7. **Verify `--mode` flag still works**:
   - Run `corpus-council query --help` — confirm `--mode` is present
   - Confirm the `query` command still accepts `--mode sequential` and `--mode consolidated` without error

8. **Verify path traversal protection**:
   - Write a temporary goal file with `persona_file: "../../etc/passwd"` in a tmp directory
   - Run `corpus-council goals process` pointing at that directory
   - Confirm non-zero exit and error message mentions the traversal

9. **Verify all quality gates**:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/
   uv run pytest
   ```
   All must exit 0.

10. **Verify no new external packages**:
    - Read `pyproject.toml` `[project.dependencies]` — confirm no new entries compared to the original (fastapi, uvicorn, typer, chromadb, sentence-transformers, anthropic, PyYAML, pydantic, python-frontmatter, prompt_toolkit)

11. **Verify the Exercise Command** from `## Dynamic Verification` in `project.md`:
    ```bash
    corpus-council goals process && corpus-council query --goal intake "test query"
    ```
    (If `ANTHROPIC_API_KEY` is set and council files exist.) If the API key is absent, confirm `goals process` exits 0 and the query command exits non-zero with a clear error about the missing API key, not a missing goal.

12. If all checks pass, emit `<task-complete>DONE</task-complete>`. If any check fails, emit `<task-blocked>` with precise detail.

## Verification
- All deliverables from project.md are implemented and confirmed
- All quality gates (`ruff`, `mypy`, `pytest`) exit 0
- `corpus-council goals process` exits 0 and produces a valid `goals_manifest.json`
- `goals_manifest.json` is byte-for-byte identical on two consecutive runs
- `corpus-council query --help` shows `--goal` and `--mode` flags
- `corpus-council query --goal nonexistent "test"` exits non-zero with a clear error
- No `"collection"` or `"conversation"` routing strings in `cli/main.py` query command or API query router
- `--mode sequential` and `--mode consolidated` still accepted by the query command
- No new packages in `pyproject.toml`
- Path traversal test rejects `../../etc/passwd` with a non-zero exit

## Done When
- [ ] Every deliverable from project.md confirmed present and working
- [ ] All quality gate commands exit 0
- [ ] Exercise command exits 0 (or exits with a clear non-goal error if API key absent)
- [ ] No regressions from the goals refactor

## Save Command
```
git add -A && git commit -m "task-00008: final validation pass — all goals deliverables confirmed"
```
