# Task 00001: Implement src/corpus_council/core/goals.py

## Role
programmer

## Objective
Create `/home/buddy/projects/corpus-council/src/corpus_council/core/goals.py` implementing the full goals model: a `GoalConfig` dataclass, a `CouncilMemberRef` dataclass, a `parse_goal_file` function that reads a goal markdown file and validates persona path containment, a `process_goals` function that reads all `.md` files from a goals directory and writes an idempotent `goals_manifest.json`, and a `load_goal` function that reads a named entry from the manifest. This module must pass `mypy` in strict mode, use `from __future__ import annotations`, and export only its public API.

## Context
Task 00000 added `goals_dir: Path`, `personas_dir: Path`, and `goals_manifest_path: Path` to `AppConfig`. This task implements the goals module that uses those paths.

**Goal file format** (markdown with YAML front matter, parsed via `python-frontmatter` already in `pyproject.toml`):
```markdown
---
desired_outcome: "Conduct a structured customer intake interview"
corpus_path: "corpus"
council:
  - persona_file: "advisor.md"
    authority_tier: 1
  - persona_file: "analyst.md"
    authority_tier: 2
---
Any additional context or instructions in the body (optional).
```

**`goals_manifest.json` schema** (array, sorted by `name` ascending, written with `json.dump(..., indent=2, sort_keys=True)` for byte-for-byte idempotency):
```json
[
  {
    "council": [
      {"authority_tier": 1, "persona_file": "advisor.md"},
      {"authority_tier": 2, "persona_file": "analyst.md"}
    ],
    "corpus_path": "corpus",
    "desired_outcome": "Conduct a structured customer intake interview",
    "name": "intake"
  }
]
```

**Path traversal validation**: Each `persona_file` value in a goal's council list must be resolved against `personas_dir` and confirmed to stay within `personas_dir`. Use the existing `validate_path_containment` in `src/corpus_council/core/validation.py`:
```python
from corpus_council.core.validation import validate_path_containment
resolved = validate_path_containment(
    personas_dir / persona_file, personas_dir, "persona_file"
)
```
Also check that the resolved path actually exists (raise `ValueError` if not).

**Idempotency**: `process_goals` must write `goals_manifest.json` atomically via a `.tmp` rename (same pattern as `FileStore.write_json`). The manifest content must be byte-for-byte identical on repeated runs. Use `json.dump(..., indent=2, sort_keys=True)` and sort the goals list by `name` before writing. Do not include timestamps or UUIDs.

**Existing utilities to reuse**:
- `validate_path_containment` from `src/corpus_council/core/validation.py`
- `python-frontmatter` (`import frontmatter`) is already in dependencies — same library used by `council.py`
- `pathlib.Path`, `json`, `dataclasses` from stdlib

**Module placement**: `/home/buddy/projects/corpus-council/src/corpus_council/core/goals.py`

**Type checking**: `from __future__ import annotations` at the top. All functions fully typed. `mypy --strict` must pass.

## Steps
1. Create `/home/buddy/projects/corpus-council/src/corpus_council/core/goals.py`.
2. Define `CouncilMemberRef` dataclass:
   ```python
   @dataclass
   class CouncilMemberRef:
       persona_file: str
       authority_tier: int
   ```
3. Define `GoalConfig` dataclass:
   ```python
   @dataclass
   class GoalConfig:
       name: str
       desired_outcome: str
       council: list[CouncilMemberRef]
       corpus_path: str
   ```
4. Implement `_validate_persona_path(persona_file: str, personas_dir: Path) -> Path`:
   - Resolve `personas_dir / persona_file` using `validate_path_containment`
   - If the resolved path does not exist, raise `ValueError(f"persona_file {persona_file!r} does not exist in personas directory")`
   - Return the resolved path
5. Implement `parse_goal_file(path: Path, personas_dir: Path) -> GoalConfig`:
   - Use `frontmatter.load(str(path))` to read the file
   - Extract `desired_outcome: str` from metadata (raise `ValueError` if missing or wrong type)
   - Extract `corpus_path: str` from metadata (raise `ValueError` if missing or wrong type)
   - Extract `council: list[...]` from metadata (raise `ValueError` if missing or not a list)
   - For each council entry, extract `persona_file: str` and `authority_tier: int`, call `_validate_persona_path`
   - Derive `name` from `path.stem`
   - Return a `GoalConfig` instance
6. Implement `process_goals(goals_dir: Path, personas_dir: Path, manifest_path: Path) -> list[GoalConfig]`:
   - Collect all `.md` files from `goals_dir` via `sorted(goals_dir.glob("*.md"))`
   - Parse each with `parse_goal_file(p, personas_dir)` — propagate any `ValueError` without catching
   - Sort the resulting `GoalConfig` list by `name` ascending
   - Serialize to a list of dicts: `[dataclasses.asdict(g) for g in goals]` — this recursively converts `CouncilMemberRef` dataclasses too
   - Write atomically: write to `manifest_path.with_suffix(".tmp")` using `json.dump(..., indent=2, sort_keys=True)`, then rename to `manifest_path` via `tmp.replace(manifest_path)`. Create parent dirs with `manifest_path.parent.mkdir(parents=True, exist_ok=True)`.
   - Return the sorted list
7. Implement `load_goal(name: str, manifest_path: Path) -> GoalConfig`:
   - Read `manifest_path` — raise `FileNotFoundError` with a clear message if absent
   - Parse the JSON array
   - Find the entry where `entry["name"] == name`
   - If not found, raise `ValueError(f"Goal {name!r} not found in manifest {manifest_path}")`
   - Reconstruct `GoalConfig` from the dict (including `CouncilMemberRef` objects from the `council` list)
   - Return it
8. Export: `__all__ = ["CouncilMemberRef", "GoalConfig", "parse_goal_file", "process_goals", "load_goal"]`
9. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/` and fix any issues.

## Verification
- Structural: file `/home/buddy/projects/corpus-council/src/corpus_council/core/goals.py` exists
- Structural: `goals.py` exports `CouncilMemberRef`, `GoalConfig`, `parse_goal_file`, `process_goals`, `load_goal`
- Structural: `goals.py` uses `from __future__ import annotations` at the top
- Structural: Grep `src/corpus_council/core/goals.py` for `validate_path_containment` — must be present (path traversal check is inside `_validate_persona_path`)
- Structural: Grep `src/corpus_council/core/goals.py` for `sort_keys=True` — must be present (idempotent manifest output)
- Behavioral: `uv run mypy src/` exits 0
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Constraint (no hardcoded behavioral rules in Python source): Grep `src/corpus_council/core/goals.py` for literal strings `"collection"` or `"conversation"` — must return no matches
- Constraint (no new external packages): `pyproject.toml` dependencies unchanged
- Constraint (path traversal prevention): `_validate_persona_path` is called for every persona reference inside `parse_goal_file`, not only at the CLI boundary
- Dynamic: Run the following Python snippet and verify it succeeds:
  ```bash
  uv run python -c "
  import tempfile, pathlib, json
  from corpus_council.core.goals import parse_goal_file, process_goals, load_goal

  with tempfile.TemporaryDirectory() as tmp:
      d = pathlib.Path(tmp)
      personas = d / 'personas'
      personas.mkdir()
      (personas / 'advisor.md').write_text('advisor content')
      goals_dir = d / 'goals'
      goals_dir.mkdir()
      (goals_dir / 'intake.md').write_text(
          '---\ndesired_outcome: \"Run intake\"\ncorpus_path: corpus\ncouncil:\n  - persona_file: advisor.md\n    authority_tier: 1\n---\n'
      )
      manifest = d / 'goals_manifest.json'
      goals = process_goals(goals_dir, personas, manifest)
      assert len(goals) == 1
      assert goals[0].name == 'intake'
      g = load_goal('intake', manifest)
      assert g.desired_outcome == 'Run intake'
      print('OK')
  "
  ```

## Done When
- [ ] `src/corpus_council/core/goals.py` exists with all five public symbols
- [ ] `parse_goal_file` validates path traversal for every persona reference
- [ ] `process_goals` produces byte-for-byte identical output on repeated runs
- [ ] `load_goal` raises `ValueError` with goal name when the named goal is absent
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/goals.py && git commit -m "task-00001: implement goals.py with parse_goal_file, process_goals, load_goal"
```
