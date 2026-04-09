# Task 00003: Update CLI — goals process subcommand and query --goal flag

## Role
programmer

## Objective
Update `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` to: (1) add a `goals` sub-app with a `process` command that calls `process_goals` and writes `goals_manifest.json`; (2) update the `query` command to require `--goal <name>`, load the named goal from the manifest, and use the goal's council and corpus configuration — removing the hardcoded collection/conversation dispatch. The existing `--mode sequential|consolidated` flag must continue to work unchanged. The `chat` and `collect` commands may remain but must not dispatch on hardcoded `"collection"` or `"conversation"` mode strings in their core orchestration path.

## Context
**Task 00000** added `goals_dir`, `personas_dir`, and `goals_manifest_path` to `AppConfig`.
**Task 00001** implemented `process_goals(goals_dir, personas_dir, manifest_path)` and `load_goal(name, manifest_path)` in `src/corpus_council/core/goals.py`.
**Task 00002** created `goals/intake.md` and `goals/create-plan.md`.

**Current CLI** is at `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py`. Key existing commands:
- `query(user_id, message, mode)` — runs `run_conversation` (no `--goal` flag yet)
- `chat(user_id, mode)` — interactive chat loop
- `collect(user_id, session, plan, mode)` — collection session
- `ingest(path)`, `embed()`, `serve(host, port)`

**The `query` command must change**: Remove the `user_id` positional argument (the goals model does not require a user_id for a single-turn query — see `api-designer.md`). Add `message: str = typer.Argument(...)` as the only positional arg. Add `goal: str = typer.Option(..., "--goal", ...)` as a required option. Keep `mode: str | None = typer.Option(None, "--mode", ...)`.

**Updated `query` command flow**:
1. Load config
2. Call `load_goal(goal, config.goals_manifest_path)` — if not found, print error to stderr and exit 1
3. Validate mode
4. Load council members from the goal's council references: for each `CouncilMemberRef` in `goal_config.council`, load the persona file from `config.personas_dir / ref.persona_file` using the existing `_parse_member` helper from `council.py` (or call `load_council` with a config pointing to the personas_dir — but it may be cleaner to load only the referenced members). The recommended approach: implement a new function `load_council_for_goal(goal_config: GoalConfig, personas_dir: Path) -> list[CouncilMember]` in `council.py` that loads only the persona files listed in the goal, sorted by `authority_tier` ascending (tier 1 = highest authority = position 1 in the deliberation hierarchy).
5. Retrieve corpus chunks using `retrieve_chunks(message, config)`
6. Run `run_deliberation` or `run_consolidated_deliberation` depending on mode
7. Print the final response

**`goals` sub-app setup**:
```python
goals_app = typer.Typer()
app.add_typer(goals_app, name="goals")

@goals_app.command("process")
def goals_process() -> None:
    """Validate and register all goal files from the configured goals directory."""
    config = _load_config_or_exit()
    try:
        results = process_goals(config.goals_dir, config.personas_dir, config.goals_manifest_path)
        typer.echo(f"Processed {len(results)} goal(s). Manifest written to {config.goals_manifest_path}")
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
```

**Imports to add**:
```python
from corpus_council.core.goals import GoalConfig, load_goal, process_goals
from corpus_council.core.council import load_council_for_goal  # new function to add
from corpus_council.core.deliberation import run_deliberation
from corpus_council.core.consolidated import run_consolidated_deliberation
from corpus_council.core.retrieval import retrieve_chunks
```

**`load_council_for_goal`** must be added to `src/corpus_council/core/council.py`. Its signature:
```python
def load_council_for_goal(goal_config: GoalConfig, personas_dir: Path) -> list[CouncilMember]:
    """Load council members referenced in a goal, sorted by authority_tier ascending."""
    ...
```
It calls `_parse_member(personas_dir / ref.persona_file, personas_dir)` for each `ref` in `goal_config.council`, sorted by `ref.authority_tier` ascending. The `authority_tier` maps directly to `position` in the deliberation pipeline (tier 1 = position 1 = synthesizer).

**No user_id in the new `query` command**: The query command is now stateless — it does not persist turn data or context. It just runs one turn and prints the result. The `run_conversation` function (which persists) is used by `chat`, not by `query`.

**Constraint**: After this change, `query` must not reference `"collection"` or `"conversation"` strings in any routing logic. The `chat` and `collect` commands may remain as-is (they serve a different purpose) but are not the focus of this task.

**mypy strict**: All new function signatures must be fully typed. `from __future__ import annotations` must be present.

## Steps
1. Add `load_council_for_goal(goal_config: GoalConfig, personas_dir: Path) -> list[CouncilMember]` to `src/corpus_council/core/council.py`. Import `GoalConfig` from `corpus_council.core.goals`. Sort members by `authority_tier` ascending. Set each member's `position` field to `ref.authority_tier` during loading (the `_parse_member` function sets `position` from the file's YAML front matter, but the goal's `authority_tier` overrides the ordering).
   - Actually, `_parse_member` reads `position` from the persona file's own YAML front matter. For the goal-driven path, the ordering is defined by `authority_tier` in the goal file, not by the persona file's `position`. So `load_council_for_goal` should load the members and then re-sort them by `ref.authority_tier` (not by the file's `position` field), and set `member.position = ref.authority_tier` to align with deliberation expectations.
   - Use Python's `dataclasses.replace(member, position=ref.authority_tier)` to produce a copy with the corrected position.
2. Update `src/corpus_council/cli/main.py`:
   a. Add imports for `GoalConfig`, `load_goal`, `process_goals` from `corpus_council.core.goals`
   b. Add import for `load_council_for_goal` from `corpus_council.core.council`
   c. Add imports for `run_deliberation` from `corpus_council.core.deliberation`, `run_consolidated_deliberation` from `corpus_council.core.consolidated`, `retrieve_chunks` from `corpus_council.core.retrieval`
   d. Create `goals_app = typer.Typer()` and `app.add_typer(goals_app, name="goals")`
   e. Implement `goals_process` command as described in Context above
   f. Replace the existing `query` command with the new signature (message only, no user_id, add --goal required option)
   g. In the `query` command body: load config, call `load_goal`, validate mode, call `load_council_for_goal`, call `retrieve_chunks`, call `run_deliberation` or `run_consolidated_deliberation`, print `result.final_response`
3. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest` and fix any issues. Note: the `query` signature change will break the existing `test_full_conversation_flow.py` only if those tests import the `query` command directly (they don't — they call `run_conversation` directly, so should be unaffected). The integration test `test_api.py` uses the HTTP API, not the CLI, so it is also unaffected.

## Verification
- Structural: `src/corpus_council/cli/main.py` defines `goals_app` and registers it with `app.add_typer(goals_app, name="goals")`
- Structural: `src/corpus_council/cli/main.py` has a `goals_process` command under `goals_app`
- Structural: The `query` command in `main.py` has a `--goal` required option and no longer takes `user_id` as a positional argument
- Structural: `src/corpus_council/core/council.py` exports `load_council_for_goal`
- Structural: Grep `src/corpus_council/cli/main.py` for `"collection"` or `"conversation"` in routing/dispatch logic — `query` command must have no such references
- Behavioral: `uv run corpus-council goals --help` exits 0 and shows `process` subcommand
- Behavioral: `uv run corpus-council query --help` exits 0 and shows `--goal` and `--mode` flags
- Behavioral: `uv run mypy src/` exits 0
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run pytest` exits 0
- Constraint (no hardcoded behavioral rules in Python source): Grep `src/corpus_council/cli/main.py` for hardcoded `"collection"` or `"conversation"` dispatch strings in the `query` command — must be absent
- Constraint (--mode flag unchanged): `--mode sequential` and `--mode consolidated` still work on the `query` command
- Constraint (no new external packages): `pyproject.toml` dependencies unchanged
- Dynamic: Run `corpus-council goals process` (after setting up goal files from Task 00002 and with persona files in `council/`) — verify exit 0 and `goals_manifest.json` is created. Since the real `council/` is empty, this command may fail if no persona files exist; in that case, create minimal test persona files first:
  ```bash
  mkdir -p council && echo -e "---\nname: Test Coach\npersona: Coach\nprimary_lens: coaching\nposition: 1\nrole_type: synthesizer\nescalation_rule: Halt if off-topic\n---\nCoach body." > council/coach.md && echo -e "---\nname: Test Analyst\npersona: Analyst\nprimary_lens: analysis\nposition: 2\nrole_type: domain_specialist\nescalation_rule: Halt if inaccurate\n---\nAnalyst body." > council/analyst.md && corpus-council goals process && test -f goals_manifest.json && echo "OK"
  ```

## Done When
- [ ] `corpus-council goals process` exits 0 and creates `goals_manifest.json`
- [ ] `corpus-council query --help` shows `--goal` and `--mode`
- [ ] `load_council_for_goal` exists in `council.py` and is fully typed
- [ ] No `"collection"` or `"conversation"` routing in the `query` command
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/cli/main.py src/corpus_council/core/council.py && git commit -m "task-00003: add goals process CLI subcommand and update query with --goal flag"
```
