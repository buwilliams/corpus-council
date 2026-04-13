# Project Spec: Sequential → Parallel Deliberation

## Goal

Replace the `sequential` deliberation mode with a `parallel` mode in which non-position-1 council members each receive the user message and corpus chunks independently (with no visibility into other members' responses), execute concurrently, and then hand all their responses to the position-1 member for final synthesis. The old sequential chain-of-thought behavior is removed entirely.

## Why This Matters

The current sequential mode feeds each member the prior members' responses before they deliberate. This contaminates their independent perspective — later members anchor to earlier ones, producing groupthink rather than genuine multi-voice deliberation. The result is functionally similar to consolidated mode but slower and more expensive. Parallel mode preserves each member's authentic, independent viewpoint and makes the council's multi-perspective design meaningful.

## Deliverables

- [ ] `llm.py` updated: `LLMClient.call()` accepts an optional `system_prompt: str` parameter; when provided it is passed as the Anthropic `system` field; the rendered template becomes the user-turn message content
- [ ] New template `templates/member_system.md`: renders a council member's system prompt from `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ goal_name }}`, `{{ goal_description }}`
- [ ] `templates/member_deliberation.md` restructured: persona/role fields removed; user-turn content is `{{ conversation_history }}`, `{{ corpus_chunks }}`, `{{ user_message }}`
- [ ] `templates/final_synthesis.md` updated: persona fields removed from user turn (they are in system prompt); user turn contains `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ member_responses }}`
- [ ] `templates/escalation_resolution.md` updated: same as above plus `{{ escalation_flags }}`
- [ ] `deliberation.py` rewritten: non-position-1 members called concurrently via `concurrent.futures.ThreadPoolExecutor`; no member sees another's response; `run_deliberation` accepts `conversation_history` and `goal` parameters and threads them to all LLM calls
- [ ] Escalation handling updated: each member may flag an escalation in their response; if any flag is raised, position-1 resolves it as part of synthesis (no mid-flight halting)
- [ ] Mode name `sequential` replaced by `parallel` everywhere: `config.yaml` default, API `mode` field, CLI `--mode` flag, docs
- [ ] `README.md` deliberation modes table updated
- [ ] All existing tests updated; new integration test covering parallel execution and escalation path

## Tech Stack

- Language: Python
- Runtime: CPython 3.12+
- Key dependencies: existing (`anthropic`, `sentence-transformers`, `chromadb`) — no new dependencies
- Concurrency: `concurrent.futures.ThreadPoolExecutor` (LLM calls are I/O-bound; thread pool fits without adding `asyncio` complexity)
- Package manager: `uv`

## Architecture Overview

**Current sequential flow (to be removed):**
Member 1 → (sees nothing) → Member 2 → (sees Member 1) → … → Position-1 synthesis. 2N+1 LLM calls, serial.

**New parallel flow:**
All non-position-1 members fire concurrently. Each member call is structured as two distinct prompt layers:
- **System prompt** (rendered from `member_system.md`): the member's persona, primary lens, role type, and the active goal's name + description
- **User turn** (rendered from `member_deliberation.md`): the conversation history, corpus chunks, and current user query

Position-1 receives all N independent responses + any escalation flags and produces the final answer using the same system/user split (`member_system.md` + `final_synthesis.md` or `escalation_resolution.md`). N+1 LLM calls, 2 serial rounds.

Escalation: each member's response may include an escalation signal. If one or more members raise it, position-1's synthesis prompt includes the escalation context and is expected to resolve it.

**LLM call structure change:** `LLMClient.call()` gains an optional `system_prompt: str` parameter. When provided it is passed as the Anthropic `system` field and the rendered template becomes the user-turn message. When absent, existing behavior is preserved (rendered template is the system prompt). The `deliberation.py` pre-renders `member_system.md` and passes the result as `system_prompt` to every LLM call.

## Testing Requirements

- Unit tests: `_format_chunks`, response parsing, escalation flag detection
- Integration tests: end-to-end `POST /query` with `mode: parallel`; assert all member responses reach position-1; assert escalation path reaches position-1 when any member flags it
- Test framework: `pytest`
- Coverage threshold: existing bar maintained
- Must not mock LLM calls in integration tests (per constitution)

## Code Quality

- Linter: `ruff`
- Formatter: `ruff format`
- Type checking: `mypy`
- Commands that must exit 0: `ruff check src/`, `ruff format --check src/`, `mypy src/`

## Constraints

- No new Python package dependencies
- No inline prompt strings — all LLM calls use `.md` templates in `templates/`
- Position-1 member never participates in the parallel deliberation phase — synthesis only
- The string `"sequential"` must not appear in user-facing config, API, or CLI after this change
- Consolidated mode is untouched

## Performance Requirements

Non-position-1 member calls execute concurrently. Wall-clock time for a 3-member council should be approximately equal to a single member call + one synthesis call (2 serial LLM round-trips), not 3 serial calls.

## Security Considerations

None beyond existing API key handling.

## Out of Scope

- Changes to consolidated mode
- Changing how corpus chunks are retrieved or ranked
- Any frontend or UI changes

## Open Questions

- None — escalation resolution during synthesis is confirmed by the user.

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- No new Python package dependencies — `pyproject.toml` dependencies must remain identical to the pre-task state
- No inline prompt strings in Python source — every LLM call must render a `.md` template from `templates/`; verify with `grep -r "anthropic" src/` finding no string literals used as prompts
- The string `"sequential"` must not appear in user-facing config keys, API request/response fields, or CLI flag names — confirm with `grep -r "sequential" src/ config.yaml` returning zero user-facing occurrences
- Position-1 member must never be submitted to the parallel deliberation phase — its role is synthesis only; confirm no ThreadPoolExecutor future is created for position-1
- No hardcoded behavioral rules, personas, or domain logic in Python source — all such rules live in council persona markdown files
- No relational database, message queue, or external service introduced — flat files plus ChromaDB remain the only persistence layer
- `ruff check src/` exits 0 with no errors
- `ruff format --check src/` exits 0 with no warnings
- `mypy src/` exits 0 with no errors (strict mode enforced via `pyproject.toml`)
- No LLM calls mocked in integration tests — all integration tests exercise real code paths against a real LLM provider

## Dynamic Verification
- **Exercise command:** `uv run pytest tests/ -m llm -x`
- **Environment:** `ANTHROPIC_API_KEY=<set in environment>`

## Execution
- **Test:** `uv run pytest tests/`
- **Typecheck:** `uv run mypy src/`
- **Lint:** `uv run ruff check src/ && uv run ruff format --check src/`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `uv run pytest tests/` exits 0. `uv run mypy src/` exits 0. `uv run ruff check src/` exits 0. `uv run ruff format --check src/` exits 0. The string `"sequential"` does not appear in any user-facing config key, API field, or CLI flag.
- **Max task tries:** 3
