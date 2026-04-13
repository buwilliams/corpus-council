# Task 00003: Rewrite deliberation.py — Parallel Mode with ThreadPoolExecutor

## Role
concurrency-engineer

## Objective
Rewrite `src/corpus_council/core/deliberation.py` to implement parallel deliberation. All non-position-1 members receive `{conversation_history, corpus_chunks, user_message}` as their user-turn content and `{member_name, persona, primary_lens, role_type, goal_name, goal_description}` as their system prompt. Members are called concurrently via `concurrent.futures.ThreadPoolExecutor`. Position-1 synthesizes all independent responses using the same system/user split. Remove `_format_prior_responses` entirely. The `escalation_check` template is still called per member, but escalation does not halt mid-flight — all members complete, and position-1 resolves any flagged escalations during synthesis. `run_deliberation` gains two new parameters: `conversation_history: str` and `goal: GoalConfig` (or equivalent typed object carrying `goal_name` and `goal_description`).

## Context
**Current file:** `src/corpus_council/core/deliberation.py`

**Current behavior (to be replaced):**
- Members iterated serially in descending position order
- Each member sees prior members' responses via `_format_prior_responses`
- Escalation causes a `break` that skips remaining members
- Uses `_format_prior_responses` helper

**New behavior:**
- `_format_prior_responses` is deleted entirely
- A new module-level function `_call_member(member, conversation_history, corpus_text, user_message, goal_name, goal_description, llm)` handles one member's LLM call + escalation check, returns a `MemberLog`
- `run_deliberation` gains new parameters: `conversation_history: str` and `goal_name: str`, `goal_description: str` (passed from `run_goal_chat` which has access to the goal object)
- `run_deliberation` pre-renders the system prompt for each call: `system_prompt = llm.render_template("member_system", system_context)` — context keys: `member_name`, `persona`, `primary_lens`, `role_type`, `goal_name`, `goal_description`
- `run_deliberation` submits one future per non-position-1 member to a `ThreadPoolExecutor`
- `ThreadPoolExecutor` used as a context manager: `with ThreadPoolExecutor(max_workers=len(others)) as executor:`
- Futures collected in a list in submission order, then `.result()` called on each inside `try/except`; any exception is re-raised directly
- After all futures complete, check if any `MemberLog.escalation_triggered` is `True`
- Build `member_responses` formatted string from all `MemberLog` entries for the synthesis context
- If any escalation: render `escalation_resolution` template as user turn; call `llm.call("escalation_resolution", user_context, system_prompt=position1_system_prompt)` — user context keys: `conversation_history`, `user_message`, `corpus_chunks`, `escalation_flags`, `member_responses`
- If no escalation: call `llm.call("final_synthesis", user_context, system_prompt=position1_system_prompt)` — user context keys: `conversation_history`, `user_message`, `corpus_chunks`, `member_responses`
- `DeliberationResult` and `MemberLog` dataclasses are unchanged in structure
- `escalating_member` on `DeliberationResult` should be the first member that triggered escalation, or `None`

**`run_deliberation` new signature:**
```python
def run_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
    conversation_history: str = "",
    goal_name: str = "",
    goal_description: str = "",
) -> DeliberationResult:
```

**`chat.py` must be updated** to pass `conversation_history`, `goal_name`, and `goal_description` to `run_deliberation`. Read `src/corpus_council/core/chat.py` to understand what goal information is available (the `GoalConfig` object has `desired_outcome` as the description). Format `conversation_history` as a plain string of prior turns (e.g., `"User: ...\nAssistant: ...\n"`).

**LLM client thread safety:** `LLMClient` is effectively thread-safe — confirmed in `llm.py`. No per-thread client instantiation needed.

**Worker function requirements:**
- Must be a module-level function (not a nested closure)
- Signature: `def _call_member(member: CouncilMember, conversation_history: str, corpus_text: str, user_message: str, goal_name: str, goal_description: str, llm: LLMClient) -> MemberLog:`
- Renders system prompt: `system_prompt = llm.render_template("member_system", {"member_name": ..., "persona": ..., "primary_lens": ..., "role_type": ..., "goal_name": ..., "goal_description": ...})`
- Calls `llm.call("member_deliberation", user_context, system_prompt=system_prompt)` — user context keys: `conversation_history`, `corpus_chunks`, `user_message`
- Calls `llm.call("escalation_check", escalation_context)` — context keys: `escalation_rule`, `member_response`
- Returns `MemberLog(member_name=..., position=..., response=..., escalation_triggered=escalation_response.startswith("TRIGGERED"))`

**Key imports needed:**
```python
from concurrent.futures import ThreadPoolExecutor, Future
```

**Type annotations:** Full annotations required (mypy strict). `Future[MemberLog]` is the future type.

**Template variable names** (must match exactly — established in tasks 00001 and 00002):
- `member_system` (system prompt): `member_name`, `persona`, `primary_lens`, `role_type`, `goal_name`, `goal_description`
- `member_deliberation` (user turn): `conversation_history`, `corpus_chunks`, `user_message`
- `final_synthesis` (user turn): `conversation_history`, `user_message`, `corpus_chunks`, `member_responses`
- `escalation_resolution` (user turn): `conversation_history`, `user_message`, `corpus_chunks`, `escalation_flags`, `member_responses`
- `escalation_check`: `escalation_rule`, `member_response`

**Helper for formatting member responses** (replaces `_format_prior_responses`):
```python
def _format_member_responses(log: list[MemberLog]) -> str:
    if not log:
        return "No member responses."
    return "\n\n".join(
        f"**{entry.member_name} (position {entry.position}):**\n{entry.response}"
        for entry in log
    )
```

**Helper for formatting escalation flags:**
```python
def _format_escalation_flags(log: list[MemberLog]) -> str:
    flagged = [e for e in log if e.escalation_triggered]
    if not flagged:
        return "No escalations flagged."
    return "\n".join(
        f"- {e.member_name} (position {e.position}): escalation triggered"
        for e in flagged
    )
```

**`__all__`** must export: `["MemberLog", "DeliberationResult", "run_deliberation"]`

Tech stack: Python 3.12, `concurrent.futures`, mypy strict.

## Steps
1. Read `src/corpus_council/core/deliberation.py` in full (to understand current structure).
2. Read `src/corpus_council/core/chat.py` in full to understand how `run_deliberation` is called and what goal/history information is available.
3. Read `src/corpus_council/core/llm.py` to confirm `render_template` is accessible (it may be a method or module-level function; use however it is currently exposed).
4. Delete `_format_prior_responses` function.
5. Add `from concurrent.futures import Future, ThreadPoolExecutor` import.
6. Write module-level `_call_member(member, conversation_history, corpus_text, user_message, goal_name, goal_description, llm) -> MemberLog` function. It must render the system prompt via `llm.render_template("member_system", ...)` and pass it to `llm.call("member_deliberation", ..., system_prompt=...)`.
7. Add `_format_member_responses` helper.
8. Add `_format_escalation_flags` helper.
9. Rewrite `run_deliberation` signature to include `conversation_history`, `goal_name`, `goal_description` parameters.
10. Rewrite `run_deliberation` body: `ThreadPoolExecutor`, parallel futures for non-position-1, collect results, post-flight escalation check, position-1 synthesis with system prompt.
11. Update `src/corpus_council/core/chat.py` to pass `conversation_history`, `goal_name` (from goal object), and `goal_description` (from `goal.desired_outcome`) to `run_deliberation`.
12. Run `uv run mypy src/` and fix any type errors.
13. Run `uv run ruff check src/ && uv run ruff format --check src/` and fix any issues.
14. Run `uv run pytest tests/ -x -k "not llm"` — deliberation tests for old sequential behavior will fail; that is expected and fixed in task 00007.

## Verification
- `grep -n "ThreadPoolExecutor" src/corpus_council/core/deliberation.py` returns at least one match
- `grep -n "asyncio\|multiprocessing\|threading.Thread" src/corpus_council/core/deliberation.py` returns no matches
- `grep -n "_format_prior_responses\|prior_responses" src/corpus_council/core/deliberation.py` returns no matches
- `grep -n "_call_member" src/corpus_council/core/deliberation.py` returns a match for the module-level function definition
- Read the `run_deliberation` function and confirm no future is submitted for the member with `position == 1`
- `uv run mypy src/` exits 0
- `uv run ruff check src/ && uv run ruff format --check src/` exits 0
- Global Constraint — No new Python package dependencies: `grep -n "ThreadPoolExecutor\|concurrent.futures" src/corpus_council/core/deliberation.py` shows only stdlib import (no new entry in `pyproject.toml` needed)
- Global Constraint — No inline prompt strings: `grep -n '"member_deliberation"\|"final_synthesis"\|"escalation_resolution"\|"escalation_check"\|"member_system"' src/corpus_council/core/deliberation.py` shows template names passed to `llm.call()` as string identifiers — confirm no multi-line prompt string literals exist
- Global Constraint — `"sequential"` absent: `grep -n "sequential" src/corpus_council/core/deliberation.py` returns no matches
- Global Constraint — Position-1 never in parallel phase: reading the submission loop confirms `position == 1` member is excluded
- Dynamic: start the server, send `POST /chat` with `mode: parallel`, verify a non-empty response is returned:
  ```bash
  uv run corpus-council serve &
  APP_PID=$!
  for i in $(seq 1 15); do curl -s http://localhost:8000/docs 2>/dev/null | grep -q "openapi" && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  RESULT=$(curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"goal":"test-goal","user_id":"user0001","message":"What is AI?","mode":"parallel"}')
  kill $APP_PID
  echo "$RESULT" | grep -q "response" || exit 1
  ```

## Done When
- [ ] `deliberation.py` uses `ThreadPoolExecutor` for non-position-1 members
- [ ] `run_deliberation` accepts `conversation_history`, `goal_name`, `goal_description`
- [ ] Each member call uses `member_system.md` as system prompt and `member_deliberation.md` as user turn
- [ ] `_format_prior_responses` is gone; `_format_member_responses` and `_format_escalation_flags` exist
- [ ] Escalation does not halt mid-flight; all members complete; escalation flags are passed to synthesis
- [ ] `chat.py` passes `conversation_history`, `goal_name`, `goal_description` to `run_deliberation`
- [ ] `uv run mypy src/` exits 0
- [ ] `uv run ruff check src/ && uv run ruff format --check src/` exits 0

## Save Command
```
git add src/corpus_council/core/deliberation.py src/corpus_council/core/chat.py && git commit -m "task-00003: rewrite deliberation.py with parallel ThreadPoolExecutor mode and system/user prompt split"
```
