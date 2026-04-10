# Task 00004: Update CLI — chat --goal, remove query and collect

## Role
programmer

## Objective
Update `src/corpus_council/cli/main.py` so that:
- The `chat` command requires `--goal <goal_name>` and `[--session <conversation_id>]` in addition to the existing `<user_id>` argument; it calls `run_goal_chat` directly (no HTTP)
- The `query` command is removed entirely
- The `collect` command is removed entirely

## Context

**File to modify:** `src/corpus_council/cli/main.py`

**Dependencies:**
- Task 00001 created `src/corpus_council/core/chat.py` with `run_goal_chat`
- Task 00003 deleted the old router files; the CLI no longer uses HTTP

**Current `chat` command** (lines 61-103) calls `run_conversation` and has no `--goal`. It must be replaced.

**New `chat` command signature:**
```python
@app.command()
def chat(
    user_id: str = typer.Argument(..., help="User identifier"),
    goal: str | None = typer.Option(None, "--goal", help="Name of the goal to use"),
    session: str | None = typer.Option(None, "--session", help="Existing conversation ID to resume"),
    mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated"),
) -> None:
```

**`--goal` enforcement:** If `goal is None`, print an error message to stderr and call `raise typer.Exit(1)`. Example:
```python
if goal is None:
    typer.echo("Error: --goal is required for chat. Use --goal <goal_name>.", err=True)
    raise typer.Exit(1)
```

**`validate_id` on `user_id`** — keep existing validation (already in the current `chat` command).

**Interactive loop:** Use `PromptSession` from `prompt_toolkit` (already imported). On first turn, use `session` as the `conversation_id` if provided, or `None` (which `run_goal_chat` will reject — actually `run_goal_chat` expects a `conversation_id` string, so the router/CLI generates a UUID before calling it). The CLI must generate a UUID if no `--session` is provided. Pattern:
```python
import uuid
conversation_id: str = session if session is not None else str(uuid.uuid4())
```
Then pass `conversation_id` to `run_goal_chat` on each turn.

**`run_goal_chat` import:**
```python
from corpus_council.core.chat import run_goal_chat
```

**Remove from imports:** `run_conversation` (from `corpus_council.core.conversation`), `start_collection`/`respond_collection` (from `corpus_council.core.collection`), `load_council_for_goal`, `run_consolidated_deliberation`, `run_deliberation`, `ChunkResult`, `retrieve_chunks` — these were used by the deleted `query` and `collect` commands. Remove all imports that become unused after the deletion.

**`collect` command removal:** Remove the entire `@app.command() def collect(...)` block (lines 149-237).

**`query` command removal:** Remove the entire `@app.command() def query(...)` block (lines 106-146).

**`load_goal` import:** `load_goal` was used by the `query` command. After removing `query`, check if `load_goal` is still needed. It is NOT needed in the new CLI (goal loading happens inside `run_goal_chat`). Remove it from imports.

**Imports to keep:** `dataclasses`, `uuid`, `Path`, `typer`, `uvicorn`, `PromptSession`, `InMemoryHistory`, `AppConfig`, `load_config`, `run_goal_chat`, `ingest_corpus`, `embed_corpus`, `process_goals`, `LLMClient`, `FileStore`, `validate_id`.

**`run_goal_chat` error handling in the interactive loop:**
```python
try:
    resp, conversation_id = run_goal_chat(
        goal_name=goal,
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
        config=config,
        store=store,
        llm=llm,
        mode=resolved_mode,
    )
    typer.echo(resp)
except KeyError as exc:
    typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(1) from exc
```

Note that `run_goal_chat` returns `tuple[str, str]` — the second element is the conversation_id (which may be the same as input, or a new UUID if it was generated upstream). For the CLI, since we generate the UUID before the first call, the returned `conversation_id` will always equal the one we passed in. Still, update the local variable from the return value for correctness.

**Tech stack:** Python 3.12, typer, prompt_toolkit, uv.

## Steps
1. Open `src/corpus_council/cli/main.py`.
2. Remove the `collect` command block entirely (the `@app.command()` decorator plus the entire function body).
3. Remove the `query` command block entirely.
4. Replace the `chat` command with the new goal-aware version as described above.
5. Update imports: remove `run_conversation`, `start_collection`, `respond_collection`, `load_council_for_goal`, `run_consolidated_deliberation`, `run_deliberation`, `ChunkResult`, `retrieve_chunks`, `load_goal`; add `run_goal_chat` from `corpus_council.core.chat`.
6. Ensure `uuid` is still imported (it was already used by `collect` but now used by the new `chat`).
7. Run `uv run corpus-council chat --help` and verify the `--goal` option appears.
8. Run `uv run corpus-council --help` and verify `query` and `collect` are not listed.
9. Run `uv run pyright src/` and confirm exit 0.
10. Run `uv run ruff check . && uv run ruff format --check .` and confirm exit 0.

## Verification
- `src/corpus_council/cli/main.py` contains no definition of a `query` command
- `src/corpus_council/cli/main.py` contains no definition of a `collect` command
- `src/corpus_council/cli/main.py` imports `run_goal_chat` from `corpus_council.core.chat`
- `src/corpus_council/cli/main.py` contains no import of `run_conversation`
- `src/corpus_council/cli/main.py` contains no import of `start_collection` or `respond_collection`
- `uv run corpus-council chat --help` exits 0 and output contains `--goal`
- `uv run corpus-council --help` exits 0 and output does NOT contain `query`
- `uv run corpus-council --help` exits 0 and output does NOT contain `collect`
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged
- Dynamic: start, exercise CLI `chat` without `--goal` exits 1, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  uv run corpus-council chat testuser 2>&1 | grep -i "goal" && echo "OK: error message mentions goal"
  EXITCODE=$(uv run corpus-council chat testuser; echo $?)
  [ "$EXITCODE" = "1" ] || (echo "Expected exit 1, got $EXITCODE" && kill $APP_PID && exit 1)
  kill $APP_PID
  ```

## Done When
- [ ] `query` and `collect` commands removed from CLI
- [ ] `chat` command requires `--goal`, supports `--session`, calls `run_goal_chat` directly
- [ ] Missing `--goal` exits 1 with error message
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/cli/main.py && git commit -m "task-00004: update CLI — chat --goal, remove query and collect commands"
```
