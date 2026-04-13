# Task 00002: Update final_synthesis.md and escalation_resolution.md Templates

## Role
programmer

## Objective
Update `templates/final_synthesis.md` and `templates/escalation_resolution.md` to:
1. Remove persona fields (`{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`) from both templates — position-1's persona is now sent as the system prompt via `member_system.md`, not in the user turn
2. Replace `{{ deliberation_log }}` with `{{ member_responses }}` in both templates
3. Replace `{{ escalation_log }}` with `{{ escalation_flags }}` in `escalation_resolution.md`
4. Add `{{ conversation_history }}` to both templates (position-1 also receives conversation history)

Both templates are user-turn content only after this task. Position-1's identity is established by the system prompt (rendered from `member_system.md` in task 00001).

## Context
Under the new parallel mode, position-1 receives all independent member responses in a single list after the parallel phase completes. The variable name changes are:
- `final_synthesis.md`: `{{ deliberation_log }}` → `{{ member_responses }}`; section heading "Council Deliberation Log" → "Independent Member Responses"
- `escalation_resolution.md`: `{{ deliberation_log }}` and `{{ prior_responses }}` (if present) → `{{ member_responses }}`; add `{{ escalation_flags }}` to the "Escalation Log" section description; add position-1 persona header (`{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`)

Current `templates/final_synthesis.md` uses:
- `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ deliberation_log }}`

After this task `final_synthesis.md` must use (persona fields gone — they are in system prompt):
- `{{ conversation_history }}`, `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ member_responses }}`

Current `templates/escalation_resolution.md` uses:
- `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ escalation_log }}`, `{{ deliberation_log }}`

After this task `escalation_resolution.md` must use (persona fields gone — they are in system prompt):
- `{{ conversation_history }}`, `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ escalation_flags }}`, `{{ member_responses }}`

The `escalation_log` context key becomes `escalation_flags`. The `deliberation_log` context key becomes `member_responses`. Persona/role fields (`member_name`, `persona`, `primary_lens`) are removed from the user turn — position-1's identity is established by the `member_system.md` system prompt rendered in `deliberation.py`.

No changes to `templates/escalation_check.md` — that template is unchanged.

Tech stack: Jinja2 markdown templates.

## Steps
1. Read `templates/final_synthesis.md` in full.
2. Remove the persona header block (`{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`).
3. Add `{{ conversation_history }}` section before the corpus material.
4. Replace `{{ deliberation_log }}` with `{{ member_responses }}` and update the section heading to "Independent Member Responses".
5. Read `templates/escalation_resolution.md` in full.
6. Remove the persona header block from this template too.
7. Add `{{ conversation_history }}` section.
8. Replace `{{ deliberation_log }}` with `{{ member_responses }}` and `{{ escalation_log }}` with `{{ escalation_flags }}`.
9. Write both updated files.
10. Confirm `deliberation_log`, `prior_responses`, `escalation_log`, `member_name`, `persona`, `primary_lens` do not appear in either updated file.

## Verification
- `grep -n "deliberation_log\|prior_responses\|escalation_log" templates/final_synthesis.md` returns no matches
- `grep -n "member_name\|persona\|primary_lens" templates/final_synthesis.md` returns no matches (persona moved to system prompt)
- `grep -n "conversation_history\|member_responses" templates/final_synthesis.md` returns matches
- `grep -n "deliberation_log\|prior_responses\|escalation_log" templates/escalation_resolution.md` returns no matches
- `grep -n "member_name\|persona\|primary_lens" templates/escalation_resolution.md` returns no matches
- `grep -n "conversation_history\|member_responses\|escalation_flags" templates/escalation_resolution.md` returns matches for all three
- Dynamic: `uv run python -c "import jinja2; e=jinja2.Environment(loader=jinja2.FileSystemLoader('templates')); t=e.get_template('final_synthesis.md'); out=t.render(conversation_history='H',user_message='Q',corpus_chunks='C',member_responses='R'); assert len(out) > 0; print('final_synthesis OK')"` exits 0
- Dynamic: `uv run python -c "import jinja2; e=jinja2.Environment(loader=jinja2.FileSystemLoader('templates')); t=e.get_template('escalation_resolution.md'); out=t.render(conversation_history='H',user_message='Q',corpus_chunks='C',escalation_flags='F',member_responses='R'); assert len(out) > 0; print('escalation_resolution OK')"` exits 0
- Global Constraint — No inline prompt strings: no Python source files changed in this task
- Global Constraint — `"sequential"` absent: no new occurrences introduced

## Done When
- [ ] `templates/final_synthesis.md` uses `{{ member_responses }}`, `{{ conversation_history }}`, no persona fields
- [ ] `templates/escalation_resolution.md` uses `{{ member_responses }}`, `{{ escalation_flags }}`, `{{ conversation_history }}`, no persona fields
- [ ] Both templates render without Jinja2 errors when provided correct context

## Save Command
```
git add templates/final_synthesis.md templates/escalation_resolution.md && git commit -m "task-00002: update synthesis and escalation templates for parallel mode and system prompt split"
```
