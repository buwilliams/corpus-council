# Project Spec: Single Persona

## Goal

End users always experience a single, coherent voice — the position-1 council member's persona. The internal council deliberation machinery is completely opaque from the outside: no response text, conversation history, or API output should reference "council members," "deliberation," "other perspectives," or any detail that reveals a multi-member architecture. The council is internal scaffolding; position-1 is the face.

## Why This Matters

The current prompt templates leak deliberation structure. `member_deliberation.md` tells each non-position-1 member "your response will be synthesized with other council members by position-1" — this primes them to write as committee contributors rather than as independent voices, subtly affecting tone. `final_synthesis.md` instructs position-1 to "resolve disagreements between council members" — this framing can produce responses that reference multiple perspectives rather than a single authoritative voice. `evaluator_consolidated.md` has no position-1 persona — it's a generic evaluator, not the designated voice. All of this can bleed into the actual responses users receive.

## Deliverables

- [ ] `src/corpus_council/templates/member_deliberation.md` updated: remove the sentence telling members their output will be synthesized with other council members by position-1. Members should analyze the query from their persona without knowing they are contributing to a multi-member synthesis.
- [ ] `src/corpus_council/templates/final_synthesis.md` updated: rename the input section from "Independent Member Responses / all council members during deliberation" to "Internal Analysis"; reframe synthesis instructions to "speak in your own voice drawing on internal analysis," removing all "council member," "deliberation," and "resolve disagreements between members" language.
- [ ] `src/corpus_council/templates/escalation_resolution.md` updated: remove "escalation was triggered during deliberation" and "Independent Member Responses" framing; reframe as position-1 addressing a critical concern using internal analysis, in its own voice.
- [ ] `src/corpus_council/templates/evaluator_consolidated.md` updated: remove "You are the evaluator... synthesizing the council's consolidated responses" preamble; rename "Council Responses" to "Internal Analysis"; remove "council members," "tensions or disagreements between members" language from instructions; frame as position-1 composing an authoritative response.
- [ ] `src/corpus_council/core/consolidated.py` updated: `run_consolidated_deliberation()` accepts `goal_name: str = ""` and `goal_description: str = ""` parameters; identifies position-1 member; builds and passes position-1's `member_system` prompt as `system_prompt` to the `evaluator_consolidated` LLM call.
- [ ] `src/corpus_council/core/chat.py` updated: passes `goal_name` and `goal_description` through to `run_consolidated_deliberation()`.
- [ ] `src/corpus_council/core/deliberation.py` updated: `_format_member_responses()` uses anonymous "Perspective N:" headers instead of member names and positions; `_format_escalation_flags()` omits member names.
- [ ] Tests updated: `tests/unit/test_consolidated.py` passes `goal_name` and `goal_description` to `run_consolidated_deliberation`; adds assertion that the `evaluator_consolidated` LLM call includes a system prompt; `tests/unit/test_deliberation.py` asserts `_format_member_responses` output does not contain member names.

## Tech Stack

- Language: Python 3.12+
- Runtime: uv, FastAPI, Uvicorn
- Key dependencies: Jinja2 (template rendering), pytest
- Build tool: uv
- Package manager: uv

## Architecture Overview

The deliberation pipeline has two modes:
- **Parallel**: N-1 members called concurrently via `ThreadPoolExecutor`; position-1 synthesizes with its own `member_system` system prompt and `final_synthesis` / `escalation_resolution` user prompt.
- **Consolidated**: one LLM call produces all member responses in a single structured output (`council_consolidated.md`); a second LLM call synthesizes (`evaluator_consolidated.md`). Currently the second call has no system prompt — it must use position-1's `member_system` prompt.

This spec changes only prompt templates and the consolidated code path. No structural changes to `DeliberationResult`, storage, or API shapes.

## Testing Requirements

- Unit tests: existing tests in `test_consolidated.py` and `test_deliberation.py` updated to match new signatures and behavior
- Test framework: pytest
- Coverage: all changed code paths covered
- What must never be mocked: nothing new — existing mock conventions apply

## Code Quality

- Linter: `uv run ruff check src/`
- Type checking: `uv run mypy src/`
- All commands: `uv run pytest && uv run mypy src/ && uv run ruff check src/`

## Constraints

- All LLM prompt changes must be in `.md` template files — no inline prompt strings in Python
- `DeliberationResult`, `MemberLog`, API response shapes, and file storage format are unchanged
- `deliberation_log` continues to be persisted to `messages.jsonl` for audit purposes — only the user-facing templates change
- `council_consolidated.md` is unchanged — it is internal parsing machinery, not user-facing output
- `escalation_check.md` is unchanged — it is internal classification, not user-facing

## Performance Requirements

None. This is a template and prompt parameter change — no new LLM calls.

## Security Considerations

None beyond what exists. No new inputs or trust boundaries.

## Out of Scope

- Changing the council architecture (still N+1 calls in parallel, 2 calls in consolidated)
- Removing `deliberation_log` from persisted storage
- Changing API request/response shapes or CLI output format
- Changes to council persona file format or `goals_manifest.json`
- Hiding council persona files from the Files tab (separate concern)

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- All LLM prompt text must live in `.md` template files under `src/corpus_council/templates/` — no inline prompt strings in Python source
- `DeliberationResult`, `MemberLog`, API response shapes, and `messages.jsonl` storage format must remain structurally unchanged
- `uv run pytest` exits 0 with no test failures
- `uv run mypy src/` exits 0 with no type errors (strict mode: `strict = true`, `python_version = "3.12"`)
- `uv run ruff check src/` exits 0 with no lint errors or warnings
- No `council_consolidated.md` or `escalation_check.md` template may be modified — they are internal parsing machinery
- No relational database, message queue, or external service dependency may be introduced — flat files and the existing LLM provider are the only infrastructure
- No hardcoded behavioral rules, personas, or domain logic in Python source — all such decisions belong to council persona markdown files

## Dynamic Verification
- **Exercise command:** `uv run pytest tests/unit/test_consolidated.py tests/unit/test_deliberation.py`

## Execution
- **Test:** `uv run pytest`
- **Typecheck:** `uv run mypy src/`
- **Lint:** `uv run ruff check src/`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `uv run pytest` exits 0. `uv run mypy src/` exits 0. `uv run ruff check src/` exits 0.
- **Max task tries:** 3
