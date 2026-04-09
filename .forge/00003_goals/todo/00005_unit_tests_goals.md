# Task 00005: Write unit tests for goals.py

## Role
tester

## Objective
Create `/home/buddy/projects/corpus-council/tests/unit/test_goals.py` with comprehensive unit tests covering all public functions in `src/corpus_council/core/goals.py`: `parse_goal_file`, `process_goals`, and `load_goal`. Also update `tests/unit/test_config.py` to assert that `load_config` correctly reads and resolves `goals_dir`, `personas_dir`, and `goals_manifest_path` from `config.yaml`. All tests must use real file I/O via `tmp_path` — no mocking of goal manifest loading, corpus retrieval, or council deliberation.

## Context
**Task 00001** created `src/corpus_council/core/goals.py` with:
- `CouncilMemberRef(persona_file: str, authority_tier: int)`
- `GoalConfig(name: str, desired_outcome: str, council: list[CouncilMemberRef], corpus_path: str)`
- `parse_goal_file(path: Path, personas_dir: Path) -> GoalConfig` — reads YAML front matter, validates persona path containment, raises `ValueError` on errors
- `process_goals(goals_dir: Path, personas_dir: Path, manifest_path: Path) -> list[GoalConfig]` — writes idempotent `goals_manifest.json`, sorted by name
- `load_goal(name: str, manifest_path: Path) -> GoalConfig` — raises `ValueError` if not found

**Goal file format** (YAML front matter in `.md` file):
```markdown
---
desired_outcome: "Run intake"
corpus_path: "corpus"
council:
  - persona_file: "advisor.md"
    authority_tier: 1
  - persona_file: "analyst.md"
    authority_tier: 2
---
Body text.
```

**Path traversal prevention**: `parse_goal_file` calls `validate_path_containment` for each `persona_file` reference. A path like `../../etc/passwd` must raise `ValueError` before any file open.

**Idempotency**: `process_goals` must produce byte-for-byte identical `goals_manifest.json` on repeated calls. The test must compare `manifest_path.read_bytes()` after both calls.

**Test naming convention**: Each test function name must describe what it asserts (e.g., `test_parse_goal_file_raises_on_path_traversal`, not `test_goal_1`).

**No mocks**: Tests must write real markdown files to `tmp_path` and call real functions. Do not use `unittest.mock`, `monkeypatch`, or any mock framework for `parse_goal_file`, `process_goals`, or `load_goal`.

**Existing test infrastructure** in `tests/conftest.py`:
- `tmp_path` fixture (from pytest) — use this for all file I/O
- `test_config: AppConfig` fixture — now has `goals_dir`, `personas_dir`, `goals_manifest_path` fields (from Task 00000)

**Test file location**: `tests/unit/test_goals.py`

**`test_config.py` addition**: Add a test `test_load_config_includes_goals_fields` that writes a full config YAML to `tmp_path` and asserts that the returned `AppConfig` has non-None, absolute `goals_dir`, `personas_dir`, and `goals_manifest_path` fields.

## Steps
1. Create `tests/unit/test_goals.py` with the following tests:

   **a. `test_parse_goal_file_happy_path`**
   - Write a goal markdown file to `tmp_path/goals/my-goal.md` with valid front matter (`desired_outcome`, `corpus_path`, `council` with two entries)
   - Write the referenced persona files to `tmp_path/personas/`
   - Call `parse_goal_file(tmp_path / "goals" / "my-goal.md", tmp_path / "personas")`
   - Assert: `result.name == "my-goal"`, `result.desired_outcome` matches the file, `len(result.council) == 2`, each `CouncilMemberRef` has correct `persona_file` and `authority_tier`

   **b. `test_parse_goal_file_raises_on_missing_persona`**
   - Write a goal file referencing `missing.md` in council list, but do NOT create that file in `personas_dir`
   - Assert `parse_goal_file(...)` raises `ValueError` with a message mentioning the missing file

   **c. `test_parse_goal_file_raises_on_path_traversal`**
   - Write a goal file with `persona_file: "../../etc/passwd"` in the council list
   - Assert `parse_goal_file(...)` raises `ValueError` (must not attempt to open the file)

   **d. `test_parse_goal_file_raises_on_missing_desired_outcome`**
   - Write a goal file with `corpus_path` and `council` but no `desired_outcome`
   - Assert `parse_goal_file(...)` raises `ValueError`

   **e. `test_process_goals_idempotent`**
   - Set up a goals directory with one goal file and matching persona files
   - Call `process_goals(goals_dir, personas_dir, manifest_path)` twice
   - Read `manifest_path.read_bytes()` after each call
   - Assert the two byte strings are equal

   **f. `test_process_goals_writes_all_goals`**
   - Set up a goals directory with two `.md` files (`alpha.md`, `beta.md`) and matching persona files
   - Call `process_goals`
   - Read and parse `goals_manifest.json`
   - Assert the manifest is a list of length 2
   - Assert entry names are `["alpha", "beta"]` (sorted ascending)
   - Assert each entry has `desired_outcome`, `corpus_path`, `council` keys

   **g. `test_process_goals_empty_dir_writes_empty_manifest`**
   - Call `process_goals` on an empty goals directory
   - Assert `goals_manifest.json` exists and contains `[]`

   **h. `test_load_goal_returns_correct_config`**
   - Write a manifest with two goals (`goal-a`, `goal-b`)
   - Call `load_goal("goal-a", manifest_path)`
   - Assert the returned `GoalConfig.name == "goal-a"` and `desired_outcome` matches

   **i. `test_load_goal_raises_on_missing_name`**
   - Write a manifest with one goal (`goal-a`)
   - Call `load_goal("nonexistent", manifest_path)`
   - Assert it raises `ValueError` with a message containing `"nonexistent"`

   **j. `test_load_goal_raises_on_missing_manifest`**
   - Call `load_goal("any", tmp_path / "nonexistent.json")`
   - Assert it raises `FileNotFoundError`

2. Update `tests/unit/test_config.py` — add test `test_load_config_includes_goals_fields`:
   - Write a full YAML config to `tmp_path/config.yaml` including `goals_dir: mygoals`, `personas_dir: mypersonas`, `goals_manifest_path: manifest.json`
   - Call `load_config(tmp_path / "config.yaml")`
   - Assert `config.goals_dir == (tmp_path / "mygoals").resolve()`
   - Assert `config.personas_dir == (tmp_path / "mypersonas").resolve()`
   - Assert `config.goals_manifest_path == (tmp_path / "manifest.json").resolve()`
   - Add a second test `test_load_config_goals_fields_use_defaults` that writes a config without those three keys and asserts the defaults are `(config_dir / "goals").resolve()`, `(config_dir / "council").resolve()`, `(config_dir / "goals_manifest.json").resolve()`

3. Run `uv run pytest tests/unit/test_goals.py tests/unit/test_config.py -v` and fix any failures.
4. Run full test suite: `uv run pytest` exits 0.
5. Run `uv run ruff check . && uv run ruff format --check .` exits 0.

## Verification
- Structural: `tests/unit/test_goals.py` exists and contains at least 10 test functions
- Structural: Every test function name starts with `test_` and describes the assertion (not just `test_goal_1`)
- Structural: No `unittest.mock`, `monkeypatch`, or `MagicMock` imports in `test_goals.py`
- Structural: `test_process_goals_idempotent` compares `manifest_path.read_bytes()` — not just exit code
- Structural: `test_parse_goal_file_raises_on_path_traversal` asserts `ValueError` is raised for a traversal path
- Behavioral: `uv run pytest tests/unit/test_goals.py -v` exits 0 with all tests passing
- Behavioral: `uv run pytest tests/unit/test_config.py -v` exits 0
- Behavioral: `uv run pytest` exits 0 (full suite)
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run mypy src/` exits 0
- Constraint (no mocking of manifest loading, corpus retrieval, council deliberation): Grep `tests/unit/test_goals.py` for `mock`, `patch`, `MagicMock` — must return no matches
- Constraint (all new public functions covered): `parse_goal_file`, `process_goals`, `load_goal` all have both happy-path and error-path tests
- Dynamic: `uv run pytest tests/unit/test_goals.py -v` — output shows all tests collected and passing

## Done When
- [ ] `tests/unit/test_goals.py` exists with ≥10 tests covering happy path, edge cases, and error cases
- [ ] `test_config.py` has tests for the three new `AppConfig` goals fields
- [ ] `uv run pytest` exits 0
- [ ] All verification checks pass

## Save Command
```
git add tests/unit/test_goals.py tests/unit/test_config.py && git commit -m "task-00005: add unit tests for goals.py and goals config fields"
```
