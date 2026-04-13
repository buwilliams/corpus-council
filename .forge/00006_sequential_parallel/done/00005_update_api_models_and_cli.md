# Task 00005: Update API Models and CLI — mode Field and --mode Flag

## Role
api-designer

## Objective
Update `src/corpus_council/api/models.py` so `ChatRequest.mode` is typed as `Literal["parallel", "consolidated"] | None` with default `None` (still optional per-request; the config default applies when `None`). Update `src/corpus_council/cli/main.py` so the `--mode` flag accepts only `"parallel"` and `"consolidated"`, not `"sequential"`, and the help text is updated. After this task, a client sending `mode: "sequential"` receives a 422 response from the API.

## Context

**File: `src/corpus_council/api/models.py`**

Current `ChatRequest`:
```python
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    user_id: str
    conversation_id: str | None = None
    message: str
    mode: str | None = None
```

The `mode` field is currently unvalidated plain `str | None`. Change it to:
```python
from typing import Literal
...
    mode: Literal["parallel", "consolidated"] | None = None
```

`Literal` is already imported in `models.py` (it's used for `FileEntry.type`). The change is purely to the `mode` field type annotation.

Pydantic will reject any value not in the Literal union with a 422 Unprocessable Entity response automatically.

**File: `src/corpus_council/cli/main.py`**

Current relevant section:
```python
mode: str | None = typer.Option(
    None, "--mode", help="Deliberation mode: sequential or consolidated"
),
```
And later:
```python
if mode is not None and mode not in {"sequential", "consolidated"}:
    typer.echo(
        f"Error: --mode must be 'sequential' or 'consolidated', got {mode!r}",
        err=True,
    )
    raise typer.Exit(1)
```

Change to:
```python
mode: str | None = typer.Option(
    None, "--mode", help="Deliberation mode: parallel or consolidated"
),
```
And:
```python
if mode is not None and mode not in {"parallel", "consolidated"}:
    typer.echo(
        f"Error: --mode must be 'parallel' or 'consolidated', got {mode!r}",
        err=True,
    )
    raise typer.Exit(1)
```

**Dependency chain:**
- Task 00003 updated `chat.py`'s `mode` default to `"parallel"`. This task updates the API/CLI layer that feeds into it.
- The router at `src/corpus_council/api/routers/chat.py` does `resolved_mode: str = request.mode or config.deliberation_mode` — no change needed there.

Tech stack: Python 3.12, FastAPI, Pydantic v2, Typer, mypy strict.

## Steps
1. Read `src/corpus_council/api/models.py` in full.
2. Change `mode: str | None = None` in `ChatRequest` to `mode: Literal["parallel", "consolidated"] | None = None`.
3. Confirm `Literal` is already imported at the top of `models.py` (it is, used by `FileEntry`).
4. Read `src/corpus_council/cli/main.py` in full.
5. Update the `--mode` help string from `"sequential or consolidated"` to `"parallel or consolidated"`.
6. Update the validation set from `{"sequential", "consolidated"}` to `{"parallel", "consolidated"}`.
7. Update the error message text to say `'parallel' or 'consolidated'`.
8. Run `uv run mypy src/` and fix any type errors.
9. Run `uv run ruff check src/ && uv run ruff format --check src/` and fix any issues.
10. Run `uv run pytest tests/ -x -k "not llm"` and verify the non-LLM tests pass.

## Verification
- `grep -n "sequential" src/corpus_council/api/models.py` returns no matches
- `grep -n "sequential" src/corpus_council/cli/main.py` returns no matches
- `grep -n 'Literal\["parallel"' src/corpus_council/api/models.py` returns a match showing the updated type annotation
- `grep -n '"parallel"' src/corpus_council/cli/main.py` returns matches for the updated help string and valid-set
- `uv run mypy src/` exits 0
- `uv run ruff check src/ && uv run ruff format --check src/` exits 0
- `uv run pytest tests/ -x -k "not llm"` exits 0
- Global Constraint — `"sequential"` absent from user-facing API/CLI: `grep -r "sequential" src/corpus_council/api/ src/corpus_council/cli/` returns no matches
- Global Constraint — No new Python package dependencies: `pyproject.toml` unchanged
- Dynamic: start the server, send `POST /chat` with `mode: "sequential"`, verify 422 response:
  ```bash
  uv run corpus-council serve &
  APP_PID=$!
  for i in $(seq 1 15); do curl -s http://localhost:8000/docs 2>/dev/null | grep -q "openapi" && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"goal":"test-goal","user_id":"user0001","message":"hi","mode":"sequential"}')
  kill $APP_PID
  [ "$STATUS" = "422" ] || { echo "Expected 422, got $STATUS"; exit 1; }
  ```

## Done When
- [ ] `ChatRequest.mode` is typed `Literal["parallel", "consolidated"] | None`
- [ ] CLI `--mode` flag rejects `"sequential"` with a clear error message
- [ ] `uv run pytest tests/ -x -k "not llm"` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/api/models.py src/corpus_council/cli/main.py && git commit -m "task-00004: update API mode field and CLI --mode flag to parallel/consolidated"
```
