# Task 00005: Add --mode flag to chat, query, and collect CLI commands

## Role
programmer

## Objective
Add a `--mode` option to the `chat`, `query`, and `collect` commands in `src/corpus_council/cli/main.py`. The option accepts `"sequential"` or `"consolidated"`. Mode is resolved via `mode or config.deliberation_mode`. An invalid provided value (not in `{"sequential", "consolidated"}`) prints an error message and exits with code 1. The resolved mode is passed to `run_conversation()`, `start_collection()`, and `respond_collection()`.

## Context

**Task 00000** added `deliberation_mode` to `AppConfig`.
**Task 00003** added `mode: str = "sequential"` to `run_conversation()`, `start_collection()`, and `respond_collection()`.

**Current CLI signatures** in `src/corpus_council/cli/main.py`:

```python
@app.command()
def chat(
    user_id: str = typer.Argument(..., help="User identifier"),
) -> None:

@app.command()
def query(
    user_id: str = typer.Argument(..., help="User identifier"),
    message: str = typer.Argument(..., help="Message to send"),
) -> None:

@app.command()
def collect(
    user_id: str = typer.Argument(..., help="User identifier"),
    session: str | None = typer.Option(None, "--session", help="Existing session ID"),
    plan: str | None = typer.Option(None, "--plan", help="Plan ID (required when no session given)"),
) -> None:
```

**Add to each command** (same pattern):
```python
mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated"),
```

**Mode resolution and validation** — after loading config:
```python
resolved_mode: str = mode or config.deliberation_mode
if mode is not None and mode not in {"sequential", "consolidated"}:
    typer.echo(f"Error: --mode must be 'sequential' or 'consolidated', got {mode!r}", err=True)
    raise typer.Exit(1)
```

Note: validate before using `resolved_mode`, and only when `mode` is explicitly provided (not when defaulting from config — config validation already happened in Task 00000).

**Call sites to update:**

In `chat`:
```python
result = run_conversation(user_id, message, config, store, llm, mode=resolved_mode)
```

In `query`:
```python
result = run_conversation(user_id, message, config, store, llm, mode=resolved_mode)
```

In `collect` — two call sites:
1. `start_collection(..., mode=resolved_mode)`
2. Both `respond_collection(...)` calls get `mode=resolved_mode`

**Current call sites** in `cli/main.py` that need updating:
- `run_conversation(user_id, message, config, store, llm)` — appears in both `chat` (line 66) and `query` (line 85)
- `start_collection(user_id=user_id, plan_id=plan, session_id=session_id, config=config, store=store, llm=llm)` (line 126)
- `respond_collection(user_id=user_id, session_id=session_id, message=first_response, config=config, store=store, llm=llm)` (line 139)
- `respond_collection(user_id=user_id, session_id=session_id, message=response, config=config, store=store, llm=llm)` (line 155)

**Global constraints:**
- `--mode` must appear on `chat`, `query`, and `collect` (all three)
- Invalid mode value prints error to stderr and exits 1
- A missing `--mode` flag never raises an error
- No new Python packages
- Code must pass `ruff check src/` and `ruff format --check src/`

## Steps

1. Open `src/corpus_council/cli/main.py`.

2. Update `chat` command:
   - Add `mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated")` as a parameter
   - After `config = _load_config_or_exit()`, add validation and resolution of `resolved_mode`
   - Update the `run_conversation()` call to pass `mode=resolved_mode`

3. Update `query` command:
   - Add `mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated")` as a parameter
   - After `config = _load_config_or_exit()`, add validation and resolution of `resolved_mode`
   - Update the `run_conversation()` call to pass `mode=resolved_mode`

4. Update `collect` command:
   - Add `mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated")` as a parameter (alongside `session` and `plan`)
   - After `config = _load_config_or_exit()`, add validation and resolution of `resolved_mode`
   - Update `start_collection(...)` to add `mode=resolved_mode`
   - Update both `respond_collection(...)` calls to add `mode=resolved_mode`

## Verification

- Structural:
  - `uv run corpus-council query --help` output contains `--mode` (Dynamic check below covers this)
  - `uv run corpus-council chat --help` output contains `--mode`
  - `uv run corpus-council collect --help` output contains `--mode`
  - `grep -c '\-\-mode' /home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` outputs at least `3` (one per command)
  - `grep -n 'resolved_mode' /home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` shows resolution in chat, query, and collect
- Global constraint — mode on all three commands:
  - `grep -n 'def chat\|def query\|def collect' /home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` and each function body contains `--mode`
- Behavioral:
  - `uv run ruff check src/corpus_council/cli/main.py` exits 0
  - `uv run ruff format --check src/corpus_council/cli/main.py` exits 0
- Dynamic: verify --help shows --mode on all three commands:
  ```bash
  cd /home/buddy/projects/corpus-council
  uv run corpus-council query --help | grep -q '\-\-mode' && echo "query --mode OK" || exit 1
  uv run corpus-council chat --help | grep -q '\-\-mode' && echo "chat --mode OK" || exit 1
  uv run corpus-council collect --help | grep -q '\-\-mode' && echo "collect --mode OK" || exit 1
  uv run corpus-council query --help | grep -q 'sequential\|consolidated' && echo "mode help text OK" || exit 1
  ```

## Done When
- [ ] `chat`, `query`, and `collect` each have `--mode` option visible in `--help`
- [ ] Mode resolves via `mode or config.deliberation_mode`
- [ ] Invalid `--mode` value exits 1 with error message to stderr
- [ ] All three commands pass `mode=resolved_mode` to the appropriate core functions
- [ ] `uv run ruff check src/corpus_council/cli/main.py` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/cli/main.py && git commit -m "task-00005: add --mode flag to chat, query, and collect CLI commands"
```
