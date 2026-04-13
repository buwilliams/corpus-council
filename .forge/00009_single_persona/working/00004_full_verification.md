# Task 00004: Full Verification Pass

## Role
product-manager

## Objective
Verify that every deliverable in `project.md` is completely and correctly implemented. Run the full quality gate, inspect each changed file, confirm leakage language is absent, and confirm out-of-scope files are untouched. No fixes in this task — if anything is missing or broken, block with a precise description of what must be corrected before this task can pass.

## Context

This is a gate task. It depends on Tasks 00001, 00002, and 00003 all being complete. It makes no code or template changes. Its only output is either `<task-complete>DONE</task-complete>` (all checks pass, all deliverables confirmed) or `<task-blocked>REASON</task-blocked>` (precise description of what is incomplete or broken).

## Steps

1. **Run the full quality gate**. All three commands must exit 0:
   ```
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```
   If any fails, block immediately with the output.

2. **Verify `member_deliberation.md`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/templates/member_deliberation.md`.
   - Confirm the sentence `Your response will be synthesized with other council members' independent responses by the position-1 authority member.` is absent.
   - Confirm all Jinja2 variables (`{{ conversation_history }}`, `{{ corpus_chunks }}`, `{{ user_message }}`) are still present.
   - Confirm the `Respond now:` line is still present.

3. **Verify `final_synthesis.md`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/templates/final_synthesis.md`.
   - Confirm `## Independent Member Responses` is replaced by `## Internal Analysis`.
   - Confirm the line `The following are the independent responses from all council members during deliberation:` is absent.
   - Confirm `Resolve any disagreements or tensions between council members` is absent.
   - Confirm instruction language speaks in position-1's own voice drawing on internal analysis.
   - Confirm `{{ member_responses }}` variable is still present (it is the data; only the framing text changes).

4. **Verify `escalation_resolution.md`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_resolution.md`.
   - Confirm `An escalation was triggered during deliberation. Details:` is absent.
   - Confirm `## Independent Member Responses` is replaced by `## Internal Analysis`.
   - Confirm `The following responses were collected before the escalation:` is absent.
   - Confirm instructions frame position-1 addressing a critical concern in its own voice.

5. **Verify `evaluator_consolidated.md`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/templates/evaluator_consolidated.md`.
   - Confirm the preamble `You are the evaluator responsible for synthesizing the council's consolidated responses into a single, authoritative final answer for the user.` is absent.
   - Confirm `## Council Responses` is replaced by `## Internal Analysis`.
   - Confirm `The following are the responses from all council members:` is absent.
   - Confirm `council members` is absent from instruction text.
   - Confirm `tensions or disagreements between members` is absent.
   - Confirm `{{ user_message }}`, `{{ council_responses }}`, and `{% if escalation_summary %}` block are still present.

6. **Run the leakage check** — must return no matches:
   ```
   grep -i "council member\|deliberation\|synthesize.*member\|resolve disagreement\|Independent Member\|evaluator.*council\|tensions.*member\|synthesized with other" /home/buddy/projects/corpus-council/src/corpus_council/templates/member_deliberation.md /home/buddy/projects/corpus-council/src/corpus_council/templates/final_synthesis.md /home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_resolution.md /home/buddy/projects/corpus-council/src/corpus_council/templates/evaluator_consolidated.md
   ```

7. **Verify `consolidated.py`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py`.
   - Confirm `run_consolidated_deliberation()` signature includes `goal_name: str = ""` and `goal_description: str = ""`.
   - Confirm position-1 member is identified from `members` (by `m.position == 1`).
   - Confirm `llm.render_template("member_system", {...})` is called with `goal_name` and `goal_description` in the context dict.
   - Confirm `llm.call("evaluator_consolidated", evaluator_context, system_prompt=position_one_system_prompt)` passes a `system_prompt` argument.

8. **Verify `chat.py`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/core/chat.py`.
   - Confirm the consolidated branch passes `goal_name=goal_name` and `goal_description=goal_config.desired_outcome` to `run_consolidated_deliberation()`.

9. **Verify `deliberation.py`**:
   - Read `/home/buddy/projects/corpus-council/src/corpus_council/core/deliberation.py`.
   - Confirm `_format_member_responses()` uses `"**Perspective {i}:**"` (or equivalent anonymous label) and does not reference `entry.member_name` or `entry.position` in the format string.
   - Confirm `_format_escalation_flags()` does not include `e.member_name` or `e.position` in the output strings.
   - Confirm `MemberLog` and `DeliberationResult` dataclass fields are unchanged.

10. **Verify test coverage**:
    - Read `/home/buddy/projects/corpus-council/tests/unit/test_consolidated.py`.
    - Confirm at least one `run_consolidated_deliberation()` call passes `goal_name` and `goal_description`.
    - Confirm at least one test asserts the `evaluator_consolidated` LLM call received a non-None, non-empty `system_prompt`.
    - Read `/home/buddy/projects/corpus-council/tests/unit/test_deliberation.py`.
    - Confirm `_format_member_responses` is imported.
    - Confirm at least one test asserts `_format_member_responses()` output does not contain member names.
    - Confirm at least one test asserts `_format_member_responses()` output contains `"Perspective 1:"`.

11. **Verify out-of-scope files are untouched**:
    - Confirm `council_consolidated.md` has not been modified: `git diff HEAD -- src/corpus_council/templates/council_consolidated.md` returns empty.
    - Confirm `escalation_check.md` has not been modified: `git diff HEAD -- src/corpus_council/templates/escalation_check.md` returns empty.
    - Confirm `pyproject.toml` dependencies are unchanged: `git diff HEAD -- pyproject.toml` returns empty or shows only task-irrelevant changes.

## Verification

- `uv run pytest` exits 0.
- `uv run mypy src/` exits 0.
- `uv run ruff check src/` exits 0.
- Leakage grep on four templates returns no matches.
- All 8 deliverable items from `project.md` confirmed complete via direct file inspection.
- No out-of-scope files modified.

## Done When
- [ ] `uv run pytest` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run ruff check src/` exits 0.
- [ ] Leakage grep returns no matches on the four modified templates.
- [ ] All 8 deliverables from `project.md` confirmed complete.
- [ ] `council_consolidated.md` unchanged.
- [ ] `escalation_check.md` unchanged.
- [ ] `pyproject.toml` unchanged.

## Save Command
```
git add .forge/00009_single_persona/ && git commit -m "task-00004: full verification pass — single-persona deliverables complete"
```
