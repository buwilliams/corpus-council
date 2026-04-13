# Task 00007: Full Verification Pass

## Role
programmer

## Objective
Run the complete verification suite (`uv run ruff check src/`, `uv run mypy src/`, `uv run pytest`) and confirm all three exit 0 with no errors or warnings. Fix any remaining issues discovered during this pass. Confirm all deliverables from the project spec are complete.

## Context
This is the final integration and verification task. All prior tasks (00000–00006) must be complete before this task runs.

**What must be true at this point**:
1. `constitution.md` has been updated with the new Core Principle, Hard Constraint, and Out-of-Scope entry.
2. `AppConfig` in `src/corpus_council/core/config.py` has no dataclass fields named `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path` — only `@property` accessors.
3. `load_config()` raises `ValueError` with the key name for each of the five removed keys if present in YAML.
4. `ingest_corpus()` accepts an optional `corpus_dir: Path | None = None` parameter.
5. `FileStore.__init__` takes a `users_dir`-style path and `user_dir()` does not prepend `/ "users"`.
6. All callsites that previously constructed `FileStore(config.data_dir)` now use `FileStore(config.users_dir)`.
7. `config.yaml` has no deprecated path keys.
8. `README.md` is updated.
9. Tests cover migration errors, derived paths, and `FileStore` with `users_dir`.

**Project root**: `/home/buddy/projects/corpus-council`

**Commands to run** (all must exit 0):
```
uv run ruff check src/
uv run mypy src/
uv run pytest
```

**Deliverables checklist from project.md**:
- [ ] `constitution.md` updated with new Core Principle, Hard Constraint, Out of Scope entries.
- [ ] `AppConfig` simplified: five fields removed, eight `@property` accessors added.
- [ ] `load_config()` raises clear `ValueError` for deprecated keys.
- [ ] All callsites updated.
- [ ] `config.yaml` updated.
- [ ] `README.md` updated.
- [ ] All existing tests pass; new tests cover simplified config, derived paths, migration errors.

## Steps
1. Run `uv run ruff check src/`. If any errors, fix them in the affected source files.
2. Run `uv run mypy src/`. If any type errors, fix them.
3. Run `uv run pytest`. If any test failures, fix the test or the code.
4. For each deliverable in the checklist above, verify it is complete:
   a. `grep -n "data_dir" /home/buddy/projects/corpus-council/.forge/constitution.md` confirms Core Principle.
   b. `grep -n "@property" /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` shows eight property definitions.
   c. `grep -n "corpus_dir\|council_dir\|goals_dir\|personas_dir\|goals_manifest_path" /home/buddy/projects/corpus-council/config.yaml` returns no matches.
   d. `grep -n "migration\|Migration" /home/buddy/projects/corpus-council/README.md` returns a match.
   e. `uv run pytest -v --tb=short` shows all tests passed.
5. If any deliverable is incomplete, perform the fix now.
6. Run all three quality commands one final time to confirm clean exit.

## Verification
- Behavioral: `uv run ruff check src/` exits 0 with no output.
- Behavioral: `uv run mypy src/` exits 0 with `Success: no issues found`.
- Behavioral: `uv run pytest` exits 0 with all tests passing (no failures, no errors).
- Structural: `grep -c "@property" /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` outputs `8` (eight property decorators).
- Structural: `grep -n "corpus_dir\|council_dir\|goals_dir\|personas_dir\|goals_manifest_path" /home/buddy/projects/corpus-council/config.yaml` returns no output.
- Structural: `grep -n "No configurable path keys" /home/buddy/projects/corpus-council/.forge/constitution.md` returns a match.
- Structural: `grep -n "ValueError\|no longer supported" /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` returns matches showing migration errors.
- Global Constraint: `diff <(grep "dependencies" /home/buddy/projects/corpus-council/pyproject.toml) <(echo "")` — no new packages added.
- Dynamic: `uv run pytest -v 2>&1 | tail -5` shows a summary line with all tests passed and 0 failed.

## Done When
- [ ] `uv run ruff check src/` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run pytest` exits 0 with all tests passing.
- [ ] All deliverables from project.md are complete.

## Save Command
```
git add -A && git commit -m "task-00007: full verification pass — all checks green"
```
