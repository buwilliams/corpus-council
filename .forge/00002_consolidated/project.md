# Project Spec: Consolidated — Two-Call Deliberation Mode

## Goal

Add a `consolidated` deliberation mode to Corpus Council that reduces every query from `2N+1` sequential LLM calls (N council members) to exactly **2 calls**: one council call that collects all member perspectives simultaneously, and one evaluator call that synthesizes them into a final response. The mode is selectable via `config.yaml` and a `--mode` CLI flag / API request field. The existing sequential mode is unchanged.

## Why This Matters

The current sequential pipeline makes 11 LLM calls for a 6-member council, taking roughly 2 minutes per query — too slow for real conversation. The consolidated mode targets sub-30-second response times by collapsing member deliberation and escalation into a single prompt, making the platform usable as an interactive conversational layer.

## Deliverables

- [ ] `src/corpus_council/core/consolidated.py` — `run_consolidated_deliberation()` function with the same signature shape as `run_deliberation()`, returning a `DeliberationResult`
- [ ] `templates/council_consolidated.md` — prompt template that concatenates all persona descriptions, requests a per-member response, and asks each member to self-report any escalation concerns
- [ ] `templates/evaluator_consolidated.md` — prompt template that receives all member responses and synthesizes a final answer, resolving any reported escalation concerns
- [ ] `src/corpus_council/core/config.py` updated — `deliberation_mode` field (`sequential` | `consolidated`, default `sequential`)
- [ ] `config.yaml` updated — `deliberation_mode: sequential` added as a documented field
- [ ] `src/corpus_council/cli/main.py` updated — `--mode sequential|consolidated` option on `chat`, `query`, and `collect` commands; CLI flag overrides `config.yaml`
- [ ] `src/corpus_council/api/` updated — optional `mode` field in request bodies for `POST /conversation`, `POST /collection/start`, `POST /collection/respond`; request field overrides `config.yaml`
- [ ] `src/corpus_council/core/conversation.py` and `collection.py` updated — pass resolved mode to deliberation dispatch
- [ ] Full test suite covering the consolidated path: council call rendering, evaluator call rendering, escalation self-report handling, and end-to-end `run_consolidated_deliberation()`
- [ ] Both modes exercised in integration tests against a real test corpus and council

## Tech Stack

- Language: Python 3.12+
- Runtime / Platform: Local / any server
- Key dependencies: FastAPI, Typer, ChromaDB, sentence-transformers, anthropic SDK, PyYAML, Jinja2, pytest
- Build tool: `uv`
- Package manager: `uv`

## Architecture Overview

### Mode Resolution

Mode is resolved in this priority order (highest wins):
1. Per-request field (`mode` in API body or `--mode` CLI flag)
2. `deliberation_mode` in `config.yaml`
3. Default: `sequential`

The resolved mode is passed as a string literal (`"sequential"` | `"consolidated"`) through `run_conversation()` and `run_collection()` to the deliberation dispatch.

### Consolidated Pipeline

```
User Message + Corpus Chunks
        │
        ▼
Council Call (1 LLM call)
  - All member personas concatenated in one prompt
  - LLM responds as each member in turn
  - Each member self-reports escalation concerns (if any)
        │
        ▼
Evaluator Call (1 LLM call)
  - Receives all member responses
  - Synthesizes final answer
  - Resolves any escalation concerns raised in step 1
        │
        ▼
Return DeliberationResult
```

### Template Design

`council_consolidated.md` receives: `members` (list of name/persona/primary_lens/role_type/escalation_rule), `user_message`, `corpus_chunks`. It instructs the LLM to produce a clearly delimited response block per member, each ending with an `ESCALATION:` line (`NONE` or a brief concern description).

`evaluator_consolidated.md` receives: `user_message`, `council_responses` (the full output of the council call), `escalation_summary` (extracted escalation lines). It instructs the LLM to synthesize a final response and resolve any escalation concerns.

### Deliberation Dispatch

`conversation.py` dispatches based on resolved mode:

```python
if mode == "consolidated":
    result = run_consolidated_deliberation(message, chunks, members, llm)
else:
    result = run_deliberation(message, chunks, members, llm)
```

Both return `DeliberationResult` — downstream persistence and response handling are unchanged.

## Testing Requirements

- Unit tests: `run_consolidated_deliberation()` with a real 2-member test council and real templates; council prompt renders all personas; evaluator prompt receives correct inputs; escalation self-report in council output is extracted and passed to evaluator
- Integration tests: full `run_conversation()` with `mode="consolidated"` against real test corpus; `POST /conversation` with `"mode": "consolidated"` returns a valid response; `uv run corpus-council query <user_id> <msg> --mode consolidated` exits 0 with output
- Test framework: pytest
- Coverage threshold: 80% minimum on `src/corpus_council/core/`
- What must never be mocked: corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB, prompt template rendering

## Code Quality

- Linter / static analysis: ruff
- Formatter: ruff format
- Type checking: mypy (strict on `core/`)
- Commands that must exit 0: `ruff check src/`, `ruff format --check src/`, `mypy src/corpus_council/core/`, `pytest`

## Constraints

- No inline prompt strings — `council_consolidated.md` and `evaluator_consolidated.md` are Jinja2 templates in `templates/`; the consolidated pipeline makes exactly 2 `llm.call()` invocations per query
- `run_consolidated_deliberation()` must return a `DeliberationResult` — the same type as `run_deliberation()` — so all downstream code (persistence, API response, CLI output) is unchanged
- Mode resolution priority (per-request → config → default) must be enforced; a missing `mode` field never errors
- No changes to the sequential deliberation path — existing behavior is preserved exactly
- `deliberation_mode` in `config.yaml` is the only new config key; no other config structure changes

## Performance Requirements

- Consolidated mode end-to-end latency (retrieval + 2 LLM calls) under 45 seconds for a 6-member council on a standard model
- Sequential mode performance is unchanged

## Security Considerations

- `mode` field in API request body is validated as an enum (`sequential` | `consolidated`); invalid values return HTTP 422
- No new API keys or external services

## Out of Scope

- Streaming LLM responses
- Async/parallel execution within either mode
- Changing the sequential deliberation pipeline
- Any frontend or UI

## Open Questions

None — all resolved.

---

## Global Constraints

The following constraints are derived from the project constitution and apply unconditionally to every task in this spec. No task output is acceptable if it violates any of these.

1. **No inline prompt strings.** Every LLM call must go through `llm.call(template_name, context)` with a Jinja2 `.md` template file in `templates/`. No f-strings or string literals may serve as prompts in Python source.
2. **No hardcoded behavioral rules in Python.** All council persona descriptions, escalation rules, role types, and lenses live in markdown files under `council/`. Python code must never contain domain-specific logic or constraints.
3. **No new infrastructure dependencies.** The consolidated mode adds no new Python packages, services, queues, or databases. All new functionality is implemented with existing dependencies (FastAPI, Typer, Jinja2, PyYAML, anthropic SDK, ChromaDB, sentence-transformers, pydantic, pytest).
4. **`DeliberationResult` is the only return type from deliberation.** `run_consolidated_deliberation()` must return `DeliberationResult` (from `src/corpus_council/core/deliberation.py`) — the identical dataclass used by `run_deliberation()`. No new return types are introduced.
5. **Exactly 2 `llm.call()` invocations per consolidated query.** The consolidated pipeline must make exactly one council call and one evaluator call — never more, never fewer. This is invariant regardless of member count or escalation.
6. **No changes to the sequential deliberation path.** `run_deliberation()`, its templates, and all sequential behavior are read-only from the perspective of this spec. The existing sequential pipeline must pass all its existing tests unchanged.
7. **Mode resolution priority is strict.** Per-request field (`mode` in API body or `--mode` CLI flag) overrides `deliberation_mode` in `config.yaml`, which overrides the default `"sequential"`. A missing or absent `mode` field at any layer must never raise an error.
8. **`deliberation_mode` is the only new config key.** No other keys are added to `config.yaml` or `AppConfig`. The `AppConfig` dataclass gains exactly one new field: `deliberation_mode: str` with default `"sequential"`.
9. **API enum validation.** The `mode` field in all API request bodies is validated as `Literal["sequential", "consolidated"]` via Pydantic. Invalid values must return HTTP 422, not 500.
10. **Real implementations only in tests.** The test suite must never mock: corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB, or prompt template rendering. LLM calls may be stubbed only in unit tests that explicitly do not carry the `llm` marker.
11. **Two interfaces, one core.** Every capability must be reachable via both the CLI (`corpus-council` entrypoint) and the API. The `--mode` flag must be present on `chat`, `query`, and `collect` commands.
12. **Python 3.12+ and `uv` throughout.** All commands use `uv run`; no direct `python` invocations. The package is built and installed via `uv`.
13. **Coverage threshold enforced.** `pytest` is configured with `--cov-fail-under=80` on `src/corpus_council/core/`. This threshold must be met with the test suite as a whole, including consolidated path tests.
14. **Mypy strict on `core/`.** All new code in `src/corpus_council/core/` must pass `mypy src/corpus_council/core/` under the `strict = true` setting in `pyproject.toml`.

---

## Dynamic Verification

These are the exact commands that must all exit 0 before any task is considered complete. Run them in order; do not skip any.

```bash
# 1. Lint
uv run ruff check src/

# 2. Format check
uv run ruff format --check src/

# 3. Type check (strict, core only)
uv run mypy src/corpus_council/core/

# 4. Full test suite (coverage enforced)
uv run pytest
```

### Per-deliverable verification checkpoints

| Deliverable | Verification |
|---|---|
| `src/corpus_council/core/consolidated.py` | `mypy src/corpus_council/core/consolidated.py`; unit tests for `run_consolidated_deliberation()` pass |
| `templates/council_consolidated.md` | Template renders without error via `llm.render_template("council_consolidated", {...})`; all member persona fields appear in output |
| `templates/evaluator_consolidated.md` | Template renders without error via `llm.render_template("evaluator_consolidated", {...})`; `escalation_summary` appears in output |
| `src/corpus_council/core/config.py` | `AppConfig` has `deliberation_mode` field; `load_config()` reads it from YAML; missing key defaults to `"sequential"` |
| `config.yaml` | `deliberation_mode: sequential` present and parseable |
| `src/corpus_council/cli/main.py` | `uv run corpus-council query --help` shows `--mode`; `uv run corpus-council chat --help` shows `--mode`; `uv run corpus-council collect --help` shows `--mode` |
| `src/corpus_council/api/models.py` | `ConversationRequest`, `CollectionStartRequest`, `CollectionRespondRequest` each have optional `mode` field; invalid value returns 422 in httpx test |
| `src/corpus_council/core/conversation.py` | `run_conversation()` accepts and passes `mode` parameter; dispatches to `run_consolidated_deliberation` when `mode="consolidated"` |
| `src/corpus_council/core/collection.py` | `start_collection()` and `respond_collection()` accept and pass `mode` parameter |
| Integration tests | `POST /conversation` with `"mode": "consolidated"` returns 200; `uv run corpus-council query <user_id> <msg> --mode consolidated` exits 0 |

---

## Execution

### Council Roster and Role Assignments

| Role | Responsibility in this spec |
|---|---|
| **programmer** | Implement `consolidated.py`, update `config.py`, `conversation.py`, `collection.py`, `cli/main.py`, `api/models.py`, and API routers |
| **tester** | Write unit and integration tests for the consolidated path; verify coverage threshold; write `conftest.py` fixtures for consolidated tests |
| **product-manager** | Verify all deliverables are present and match the spec; guard against scope creep into the sequential path; confirm mode resolution priority is correctly implemented |
| **api-designer** | Define the `mode` field shape in `ConversationRequest`, `CollectionStartRequest`, `CollectionRespondRequest`; confirm CLI flag interface on all three commands |
| **data-engineer** | Confirm no new storage schema changes are needed; verify `FileStore` and JSONL persistence is unchanged for consolidated mode results |
| **security-engineer** | Validate that `mode` is a closed enum in all API models; confirm no injection risk in template rendering with member persona data |

### Task Sequence

Tasks must be executed in this order. Each task may only begin after all tasks it depends on are complete and verified.

**Task 1 — Config extension** (`programmer`)
- Add `deliberation_mode: str = "sequential"` to `AppConfig` in `src/corpus_council/core/config.py`
- Update `load_config()` to read `deliberation_mode` from YAML with default `"sequential"`; validate it is one of `"sequential"` or `"consolidated"`
- Add `deliberation_mode: sequential` with explanatory comment to `config.yaml`
- Verification: `mypy src/corpus_council/core/config.py`; existing config tests pass

**Task 2 — Templates** (`programmer`, reviewed by `api-designer`)
- Create `templates/council_consolidated.md` — Jinja2 template receiving `members`, `user_message`, `corpus_chunks`; produces one delimited block per member ending with `ESCALATION: NONE` or `ESCALATION: <concern>`
- Create `templates/evaluator_consolidated.md` — Jinja2 template receiving `user_message`, `council_responses`, `escalation_summary`; synthesizes final answer and resolves any escalation concerns
- Verification: templates render without Jinja2 errors with sample data; no Python string templating used

**Task 3 — `consolidated.py`** (`programmer`, reviewed by `data-engineer`)
- Create `src/corpus_council/core/consolidated.py` implementing `run_consolidated_deliberation(user_message, corpus_chunks, members, llm) -> DeliberationResult`
- Makes exactly 2 `llm.call()` invocations: first `"council_consolidated"`, then `"evaluator_consolidated"`
- Parses `ESCALATION:` lines from council output; builds `escalation_summary` string for evaluator
- Builds `deliberation_log` as a list of `MemberLog` entries (one per member parsed from council output)
- Returns `DeliberationResult` with `final_response`, `deliberation_log`, `escalation_triggered`, `escalating_member`
- Verification: `mypy src/corpus_council/core/consolidated.py`; unit tests pass

**Task 4 — Deliberation dispatch in `conversation.py` and `collection.py`** (`programmer`)
- Update `run_conversation()` signature to accept `mode: str = "sequential"` parameter
- Add dispatch: `if mode == "consolidated": result = run_consolidated_deliberation(...)` else `result = run_deliberation(...)`
- Update `start_collection()` and `respond_collection()` to accept and thread `mode` parameter similarly
- Verification: `mypy src/corpus_council/core/conversation.py`; existing conversation tests pass

**Task 5 — API models and routers** (`api-designer`, implemented by `programmer`, reviewed by `security-engineer`)
- Add `mode: Literal["sequential", "consolidated"] | None = None` to `ConversationRequest`, `CollectionStartRequest`, `CollectionRespondRequest` in `src/corpus_council/api/models.py`
- Update `src/corpus_council/api/routers/conversation.py` to resolve mode: `request.mode or config.deliberation_mode`; pass resolved mode to `run_conversation()`
- Update `src/corpus_council/api/routers/collection.py` similarly for `start_collection()` and `respond_collection()`
- Verification: invalid `mode` value returns HTTP 422 in httpx test; valid `mode` is forwarded correctly

**Task 6 — CLI** (`api-designer`, implemented by `programmer`)
- Add `mode: str | None = typer.Option(None, "--mode", help="Deliberation mode: sequential or consolidated")` to `chat`, `query`, and `collect` commands in `src/corpus_council/cli/main.py`
- Resolve mode: `mode or config.deliberation_mode`; pass to `run_conversation()` / `start_collection()` / `respond_collection()`
- Validate CLI mode value: if provided and not in `{"sequential", "consolidated"}`, print error and exit 1
- Verification: `uv run corpus-council query --help` shows `--mode`; `uv run corpus-council query <user_id> <msg> --mode consolidated` exits 0 with output

**Task 7 — Test suite** (`tester`)
- Unit tests (no real LLM calls):
  - `council_consolidated.md` renders all member personas given a 2-member list
  - `evaluator_consolidated.md` renders with `council_responses` and `escalation_summary` inputs
  - `run_consolidated_deliberation()` with a stubbed `LLMClient.call` that returns a known string: verify exactly 2 calls made, `DeliberationResult` returned, escalation parsing works
- Integration tests (marked `llm`, require `ANTHROPIC_API_KEY`):
  - `run_conversation(user_id, message, config, store, llm, mode="consolidated")` against real test corpus and council; returns `ConversationResult` with non-empty response
  - `POST /conversation` with `"mode": "consolidated"` against test API; returns 200 with `response` field
  - `uv run corpus-council query <user_id> <msg> --mode consolidated` exits 0 with printed output
- Verification: `uv run pytest`; `--cov-fail-under=80` passes

**Task 8 — Final verification** (`product-manager`, `security-engineer`)
- Run full dynamic verification suite: ruff check, ruff format --check, mypy, pytest
- Confirm all deliverables checklist items are ticked
- Confirm sequential mode tests still pass unchanged
- Confirm no new dependencies added to `pyproject.toml`
- Confirm `mode` invalid value returns HTTP 422 (not 500) via httpx

### File Map

New files to create:
- `/home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py`
- `/home/buddy/projects/corpus-council/templates/council_consolidated.md`
- `/home/buddy/projects/corpus-council/templates/evaluator_consolidated.md`

Files to modify:
- `/home/buddy/projects/corpus-council/src/corpus_council/core/config.py` — add `deliberation_mode` field
- `/home/buddy/projects/corpus-council/config.yaml` — add `deliberation_mode: sequential`
- `/home/buddy/projects/corpus-council/src/corpus_council/core/conversation.py` — add `mode` parameter and dispatch
- `/home/buddy/projects/corpus-council/src/corpus_council/core/collection.py` — add `mode` parameter and pass-through
- `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` — add `--mode` option to `chat`, `query`, `collect`
- `/home/buddy/projects/corpus-council/src/corpus_council/api/models.py` — add `mode` field to request models
- `/home/buddy/projects/corpus-council/src/corpus_council/api/routers/conversation.py` — resolve and forward mode
- `/home/buddy/projects/corpus-council/src/corpus_council/api/routers/collection.py` — resolve and forward mode

Test files to create or extend:
- `/home/buddy/projects/corpus-council/tests/unit/test_consolidated.py`
- `/home/buddy/projects/corpus-council/tests/integration/test_consolidated_integration.py`
