# Task 00023: Replace sys.stdin Input with prompt_toolkit in CLI

## Role
programmer

## Objective
Replace the raw `sys.stdin` line-by-line reading in `src/corpus_council/cli/main.py` with `prompt_toolkit` for both the `chat` and `collect` commands. The result is a CLI that supports readline-style editing, arrow key history navigation, Ctrl+C (KeyboardInterrupt) to exit gracefully, and Ctrl+D (EOFError) to signal end of input. Add `prompt_toolkit>=3.0` as a runtime dependency in `pyproject.toml`.

## Context
The current `chat` command loops over `sys.stdin` with `for line in sys.stdin:` and the `collect` command calls `sys.stdin.readline()` directly. Neither approach supports arrow keys, history navigation, or proper terminal control sequences.

`prompt_toolkit` is the standard Python library for rich terminal input. The key API is:

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

session: PromptSession[str] = PromptSession(history=InMemoryHistory())
# In a loop:
try:
    text = session.prompt("> ")
except KeyboardInterrupt:
    break   # Ctrl+C: discard current line, continue or exit
except EOFError:
    break   # Ctrl+D: end of input
```

`PromptSession` with `InMemoryHistory` gives up/down arrow key history navigation within a single CLI session at no extra cost. `session.prompt(...)` returns the entered string already stripped of the trailing newline.

File to modify: `src/corpus_council/cli/main.py`
Dependency file to modify: `pyproject.toml`

The existing imports at the top of `main.py` include `import sys` — this import can be removed entirely after the replacement since no other code in the file uses `sys`.

Current `chat` command input loop (lines 53–60 of `main.py`):
```python
for line in sys.stdin:
    message = line.rstrip("\n")
    if message in ("quit", "exit"):
        break
    if not message:
        continue
    result = run_conversation(user_id, message, config, store, llm)
    typer.echo(f"> {result.response}")
```

Current `collect` command first-response read (lines 108–119):
```python
first_line = sys.stdin.readline()
if not first_line:
    return
first_response = first_line.rstrip("\n")
collection_session = respond_collection(...)
```

Current `collect` command continuation loop (lines 121–135):
```python
while collection_session.status != "complete":
    if collection_session.next_prompt:
        typer.echo(collection_session.next_prompt)
    line = sys.stdin.readline()
    if not line:
        break
    response = line.rstrip("\n")
    collection_session = respond_collection(...)
```

Both commands must use a single shared `PromptSession` instance created once per command invocation.

Tech stack: Python 3.12+, Typer, uv, ruff, mypy strict mode.

## Steps

1. Add `prompt_toolkit>=3.0` to the `dependencies` list in `pyproject.toml` (inside the `[project]` table, not the dev extras). Run `uv sync` so the lock file and environment are updated.

2. In `src/corpus_council/cli/main.py`:
   a. Remove `import sys` from the imports section.
   b. Add `from prompt_toolkit import PromptSession` and `from prompt_toolkit.history import InMemoryHistory` to the imports section. Place them after the stdlib imports and before the third-party imports, following the existing import ordering (ruff enforces isort-compatible `I` rules).
   c. Replace the `chat` command's input loop with a `PromptSession`-based loop:
      - Create `session: PromptSession[str] = PromptSession(history=InMemoryHistory())` before the loop.
      - Use `while True:` with `session.prompt("You: ")` (or any short prompt string).
      - Catch `KeyboardInterrupt` to `continue` (discard current input, keep the loop running) or `break` — either is acceptable; catching `EOFError` must `break`.
      - Keep the `"quit"` / `"exit"` string check and the empty-message `continue` guard.
   d. Replace the `collect` command's two `sys.stdin` reads with a single `PromptSession` instance:
      - Create `session: PromptSession[str] = PromptSession(history=InMemoryHistory())` once before any input is needed.
      - Replace the `sys.stdin.readline()` / empty-check / `.rstrip("\n")` pattern with `session.prompt("")` wrapped in `try/except EOFError: break` (and `KeyboardInterrupt: break`).
      - Apply the same pattern to the continuation loop.

3. Verify the file has no remaining references to `sys.stdin`.

## Verification

- Structural: file `src/corpus_council/cli/main.py` exists and contains no reference to `sys.stdin`:
  ```
  grep -n 'sys\.stdin' src/corpus_council/cli/main.py
  ```
  must return no matches.

- Structural: `main.py` imports `PromptSession` from `prompt_toolkit`:
  ```
  grep -n 'from prompt_toolkit' src/corpus_council/cli/main.py
  ```
  must show at least `from prompt_toolkit import PromptSession`.

- Structural: `pyproject.toml` lists `prompt_toolkit` as a runtime dependency:
  ```
  grep 'prompt_toolkit' pyproject.toml
  ```
  must return a match inside the `[project]` `dependencies` list.

- Global Constraint — no inline prompt strings: confirm no string literals are passed directly to LLM client call sites in modified files:
  ```
  grep -n 'llm\.' src/corpus_council/cli/main.py
  ```
  `main.py` passes the `llm` object to core functions; it must not call `llm.complete(` or similar with inline strings. Verify the pattern is unchanged.

- Global Constraint — no API keys in source: confirm `main.py` contains no assignments of the form `api_key =` or `ANTHROPIC_API_KEY =`:
  ```
  grep -n 'api_key\s*=' src/corpus_council/cli/main.py
  ```
  must return no matches.

- Global Constraint — ruff lint and format:
  ```
  uv run ruff check src/
  uv run ruff format --check src/
  ```
  both must exit 0.

- Global Constraint — mypy strict on core (cli is outside strict scope but must not break imports):
  ```
  uv run mypy src/corpus_council/core/
  ```
  must exit 0.

- Global Constraint — pytest:
  ```
  uv run pytest
  ```
  must exit 0 with all tests passing and coverage >= 80% on `src/corpus_council/core/`.

- Dynamic: invoke the CLI `chat` command with a piped input sequence and verify it responds then exits cleanly:
  ```bash
  printf 'hello\nquit\n' | uv run corpus-council chat testuser123 2>&1 | grep -q 'Welcome'
  ```
  must exit 0 (the welcome banner is always printed regardless of input source, confirming the command launched and ran the input loop).

## Done When
- [ ] `src/corpus_council/cli/main.py` uses `PromptSession` from `prompt_toolkit` for all user input in `chat` and `collect`; no `sys.stdin` references remain
- [ ] `prompt_toolkit>=3.0` is listed as a runtime dependency in `pyproject.toml` and `uv sync` has been run
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/cli/main.py pyproject.toml uv.lock && git commit -m "task-00023: replace sys.stdin with prompt_toolkit for arrow key and ctrl key support in CLI"
```
