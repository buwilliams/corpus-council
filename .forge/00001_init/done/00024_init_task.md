# Task 00024: Add `query` CLI Command for One-Shot Conversation

## Role
programmer

## Objective
Add a `query` command to the Typer CLI in `src/corpus_council/cli/main.py` that accepts a `user_id` and a `message` string as positional arguments, runs the full council deliberation once via `run_conversation`, prints the response to stdout, and exits. No interactive loop, no prompting — single call, single response, clean exit.

## Context
The existing CLI at `src/corpus_council/cli/main.py` already has a `chat` command that runs an interactive `PromptSession` loop. The `query` command is a non-interactive variant: it takes the message directly as a CLI argument, calls `run_conversation` exactly once, and exits. This is useful for scripting, piping, and one-shot lookups without entering an interactive session.

`run_conversation` signature (from `src/corpus_council/core/conversation.py`):
```python
def run_conversation(
    user_id: str,
    message: str,
    config: AppConfig,
    store: FileStore,
    llm: LLMClient,
) -> ConversationResult:
    ...
```
`ConversationResult.response` is a `str`.

`validate_id` is imported from `src/corpus_council/core/validation.py` and raises `ValueError` on invalid input. It is already used in the `chat` and `collect` commands.

The Typer app is declared at module level as `app = typer.Typer(name="corpus-council", no_args_is_help=True)`. Add the new command by decorating a function with `@app.command()`.

No new imports are needed — all required symbols (`run_conversation`, `validate_id`, `FileStore`, `LLMClient`, `_load_config_or_exit`) are already imported or defined in `main.py`.

Tech stack: Python 3.12+, Typer, uv, ruff, mypy strict mode.

## Steps

1. Open `src/corpus_council/cli/main.py` and add the following command function after the `chat` command (before `collect`):

```python
@app.command()
def query(
    user_id: str = typer.Argument(..., help="User identifier"),
    message: str = typer.Argument(..., help="Message to send"),
) -> None:
    """Send a single message and print the response, then exit."""
    try:
        validate_id(user_id, "user_id")
    except ValueError as exc:
        typer.echo(f"Invalid user_id: {exc}", err=True)
        raise typer.Exit(1) from exc

    config = _load_config_or_exit()
    store = FileStore(config.data_dir)
    llm = LLMClient(config)
    result = run_conversation(user_id, message, config, store, llm)
    typer.echo(result.response)
```

2. No other files need modification. Do not add imports (all are already present). Do not remove or change any existing command.

## Verification

- Structural: `src/corpus_council/cli/main.py` contains a function named `query` decorated with `@app.command()`:
  ```
  grep -n 'def query' src/corpus_council/cli/main.py
  ```
  must return a match.

- Structural: the `query` command is visible in the CLI help output:
  ```bash
  uv run corpus-council --help
  ```
  output must include `query`.

- Structural: no inline LLM prompt strings introduced — `query` calls `run_conversation`, not `llm.*` directly:
  ```
  grep -n 'llm\.' src/corpus_council/cli/main.py
  ```
  must return no new direct `llm.complete(` or `llm.call(` calls in the added function.

- Global Constraint — no API keys in source:
  ```
  grep -n 'api_key\s*=' src/corpus_council/cli/main.py
  ```
  must return no matches.

- Global Constraint — no relational DB:
  ```
  grep -n 'sqlite3\|psycopg\|mysql' src/corpus_council/cli/main.py
  ```
  must return no matches.

- Global Constraint — ruff lint:
  ```
  uv run ruff check src/
  ```
  must exit 0.

- Global Constraint — ruff format:
  ```
  uv run ruff format --check src/
  ```
  must exit 0.

- Global Constraint — mypy strict on core (cli must not break core imports):
  ```
  uv run mypy src/corpus_council/core/
  ```
  must exit 0.

- Global Constraint — pytest:
  ```
  uv run pytest
  ```
  must exit 0 with all tests passing and coverage >= 80% on `src/corpus_council/core/`.

- Dynamic: invoke `query` with real arguments and verify it prints a non-empty response and exits 0:
  ```bash
  uv run corpus-council query testuser001 "What is this system?" 2>&1 | grep -qv '^$'
  ```
  The command must exit 0 and produce at least one non-empty line of output.

## Done When
- [ ] `src/corpus_council/cli/main.py` contains a `query` command that accepts `user_id` and `message` positional arguments, calls `run_conversation` once, prints `result.response`, and exits
- [ ] `uv run corpus-council --help` lists `query` as a command
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/cli/main.py && git commit -m "task-00024: add query CLI command for one-shot conversation"
```
