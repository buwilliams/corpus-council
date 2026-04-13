# Task 00002: Update consolidated.py, chat.py, and deliberation.py

## Role
programmer

## Objective
Thread `goal_name` and `goal_description` into the consolidated deliberation path; pass position-1's rendered `member_system` prompt as the `system_prompt` to the evaluator LLM call; and anonymize member response headers in `_format_member_responses()` and `_format_escalation_flags()`.

## Context

**Files to modify:**
- `/home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py`
- `/home/buddy/projects/corpus-council/src/corpus_council/core/chat.py`
- `/home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py`

**Do not modify any `.md` template files** — those are covered by Task 00001.

**Current signatures and behaviors:**

`run_consolidated_deliberation()` in `consolidated.py`:
```python
def run_consolidated_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
) -> DeliberationResult:
```
The evaluator LLM call currently passes no `system_prompt`:
```python
final_response = llm.call("evaluator_consolidated", evaluator_context)
```

`run_goal_chat()` in `chat.py` — the consolidated branch:
```python
if mode == "consolidated":
    result = run_consolidated_deliberation(message, chunks, members, llm)
```
The parallel branch already passes `goal_name=goal_name` and `goal_description=goal_config.desired_outcome` to `run_deliberation()`.

`_format_member_responses()` in `deliberation.py` — current output format:
```python
f"**{entry.member_name} (position {entry.position}):**\n{entry.response}"
```

`_format_escalation_flags()` in `deliberation.py` — current output format:
```python
f"- {e.member_name} (position {e.position}): escalation triggered"
```

**How position-1 is identified in the parallel path** (model to follow):
```python
sorted_members = sorted(members, key=lambda m: m.position, reverse=True)
position_one = next(m for m in sorted_members if m.position == 1)
```
Then the system prompt is built via:
```python
position_one_system_prompt = llm.render_template(
    "member_system",
    {
        "member_name": position_one.name,
        "persona": position_one.persona,
        "primary_lens": position_one.primary_lens,
        "role_type": position_one.role_type,
        "goal_name": goal_name,
        "goal_description": goal_description,
    },
)
```

**`member_system.md` template variables** (confirmed from reading the file):
- `{{ member_name }}`
- `{{ persona }}`
- `{{ primary_lens }}`
- `{{ role_type }}`
- `{{ goal_name }}`
- `{{ goal_description }}`

**`evaluator_consolidated.md` template variables** (after Task 00001 updates):
- `{{ user_message }}`
- `{{ council_responses }}` — name is unchanged (carries raw council output)
- `{{ escalation_summary }}` — in the conditional block `{% if escalation_summary %}`

The `evaluator_consolidated` template does NOT use `goal_name` or `goal_description` as Jinja2 variables — those go into the `system_prompt` via `member_system.md`. Do not add them to the evaluator context dict.

**`DeliberationResult` and `MemberLog` shapes must remain unchanged.** Do not add, remove, or rename any fields.

## Steps

1. **Read all three files** before editing:
   - `/home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py`
   - `/home/buddy/projects/corpus-council/src/corpus_council/core/chat.py`
   - `/home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py`

2. **Update `src/corpus_council/core/consolidated.py`**:

   a. Add `goal_name: str = ""` and `goal_description: str = ""` as keyword-with-default parameters to `run_consolidated_deliberation()`. Place them after `llm: LLMClient`. Full new signature:
   ```python
   def run_consolidated_deliberation(
       user_message: str,
       corpus_chunks: list[ChunkResult],
       members: list[CouncilMember],
       llm: LLMClient,
       goal_name: str = "",
       goal_description: str = "",
   ) -> DeliberationResult:
   ```

   b. After the existing `corpus_text = _format_chunks(corpus_chunks)` line, identify position-1 and build its system prompt (insert before Call 1):
   ```python
   position_one = next(m for m in members if m.position == 1)
   position_one_system_prompt = llm.render_template(
       "member_system",
       {
           "member_name": position_one.name,
           "persona": position_one.persona,
           "primary_lens": position_one.primary_lens,
           "role_type": position_one.role_type,
           "goal_name": goal_name,
           "goal_description": goal_description,
       },
   )
   ```

   c. Pass `system_prompt=position_one_system_prompt` to the evaluator LLM call (Call 2):
   ```python
   final_response = llm.call(
       "evaluator_consolidated",
       evaluator_context,
       system_prompt=position_one_system_prompt,
   )
   ```

   d. Keep `evaluator_context` unchanged — it still uses `user_message`, `council_responses`, and `escalation_summary`. Do NOT add `goal_name` or `goal_description` to the evaluator context dict.

3. **Update `src/corpus_council/core/chat.py`**:

   Find the consolidated branch (line ~77):
   ```python
   if mode == "consolidated":
       result = run_consolidated_deliberation(message, chunks, members, llm)
   ```
   Update it to pass the new parameters:
   ```python
   if mode == "consolidated":
       result = run_consolidated_deliberation(
           message,
           chunks,
           members,
           llm,
           goal_name=goal_name,
           goal_description=goal_config.desired_outcome,
       )
   ```
   `goal_name` is already available as a parameter of `run_goal_chat()`. `goal_config.desired_outcome` is already used in the parallel branch.

4. **Update `src/corpus_council/core/deliberation.py`**:

   a. Update `_format_member_responses()` — replace the f-string header from member name/position to anonymous `Perspective N:` (1-based index):
   ```python
   def _format_member_responses(log: list[MemberLog]) -> str:
       if not log:
           return "No member responses."
       return "\n\n".join(
           f"**Perspective {i}:**\n{entry.response}"
           for i, entry in enumerate(log, start=1)
       )
   ```
   The response content (`entry.response`) must be preserved exactly. Only the header changes.

   b. Update `_format_escalation_flags()` — remove member names, keep only the flag content. The flagged entries currently have `escalation_triggered=True` but no text content beyond that; the function produces a simple list:
   ```python
   def _format_escalation_flags(log: list[MemberLog]) -> str:
       flagged = [e for e in log if e.escalation_triggered]
       if not flagged:
           return "No escalations flagged."
       return "\n".join(
           "- escalation triggered"
           for _ in flagged
       )
   ```
   This removes `{e.member_name} (position {e.position}):` from each flag line. The count of flagged entries is still conveyed by the number of bullet lines.

5. **Run verification** before declaring done.

## Verification

Run all three checks and confirm each exits 0:
```
uv run ruff check src/
uv run mypy src/
uv run pytest
```

Also verify structurally:
- `grep -n "goal_name\|goal_description" /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` shows both parameters in the function signature and in the `render_template` context.
- `grep -n "run_consolidated_deliberation" /home/buddy/projects/corpus-council/src/corpus_council/core/chat.py` shows `goal_name=goal_name` and `goal_description=goal_config.desired_outcome` being passed.
- `grep -n "member_name\|position" /home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py` shows `_format_member_responses` no longer references `entry.member_name` or `entry.position` in the format string.
- `grep -n "Perspective" /home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py` shows `"**Perspective {i}:**"` in `_format_member_responses`.
- No new packages in `pyproject.toml`.
- No inline prompt strings introduced in Python source.

## Done When
- [ ] `run_consolidated_deliberation()` accepts `goal_name: str = ""` and `goal_description: str = ""`.
- [ ] Position-1 member identified from `members` list and `member_system` prompt rendered with `goal_name`/`goal_description`.
- [ ] Evaluator LLM call passes `system_prompt=position_one_system_prompt` (non-empty when a valid position-1 member exists).
- [ ] `chat.py` passes `goal_name=goal_name` and `goal_description=goal_config.desired_outcome` to `run_consolidated_deliberation()`.
- [ ] `_format_member_responses()` uses `"**Perspective {i}:**"` headers; member names and positions absent from output.
- [ ] `_format_escalation_flags()` omits member names; only flag signal lines remain.
- [ ] `DeliberationResult` and `MemberLog` fields unchanged.
- [ ] `uv run ruff check src/` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run pytest` exits 0.

## Save Command
```
git add src/corpus_council/core/consolidated.py src/corpus_council/core/chat.py src/corpus_council/core/deliberation.py && git commit -m "task-00002: thread goal params and position-1 system prompt through consolidated path; anonymize member response headers"
```
