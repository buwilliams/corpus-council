# Task 00001: Create member_system.md and Restructure member_deliberation.md

## Role
programmer

## Objective
Create a new template `templates/member_system.md` that renders a council member's system prompt from their persona and the active goal. Restructure `templates/member_deliberation.md` so it renders the user-turn content only: conversation history, corpus chunks, and the current user query. Remove all persona/role fields and the `prior_responses` section from `member_deliberation.md`. After this task, every member LLM call will pass `member_system.md` output as the Anthropic `system` field and `member_deliberation.md` output as the user-turn message.

## Context

**Two files to produce:**

**1. New file `templates/member_system.md`**

This template renders the council member's identity and mission as a system prompt. Variables: `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ goal_name }}`, `{{ goal_description }}`.

Write it as a concise, direct identity statement — not a set of instructions, but who the member is and what they are here to accomplish. Example structure:

```
You are **{{ member_name }}**.

**Persona:** {{ persona }}
**Primary Lens:** {{ primary_lens }}
**Role Type:** {{ role_type }}

**Your mission for this conversation:**
{{ goal_description }}
```

Keep it tight — this is a system prompt, not a deliberation prompt.

**2. Updated file `templates/member_deliberation.md`**

This template renders the user-turn message: what the member receives as input to deliberate on. Variables: `{{ conversation_history }}`, `{{ corpus_chunks }}`, `{{ user_message }}`.

Remove entirely: `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ prior_responses }}`, the "Prior Council Responses" section.

Add: `{{ conversation_history }}` section showing prior turns of the conversation (may be empty for the first turn).

Example structure:

```
## Conversation History
{{ conversation_history }}

## Relevant Corpus Material
{{ corpus_chunks }}

## Current Query
{{ user_message }}

## Instructions
Based on your persona and mission (provided in your system context), give your independent analysis of the current query. Draw on the corpus material and conversation history above. Do not speculate beyond what the corpus supports.

Your response will be synthesized with other council members' independent responses by the position-1 authority member.

Respond now:
```

**Current `templates/member_deliberation.md`** (read before editing):
- Contains: `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ user_message }}`, `{{ corpus_chunks }}`, `{{ prior_responses }}`
- Has a "Prior Council Responses" section — remove entirely

After this task:
- `member_system.md` must exist and contain: `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ goal_name }}`, `{{ goal_description }}`
- `member_deliberation.md` must contain: `{{ conversation_history }}`, `{{ corpus_chunks }}`, `{{ user_message }}`
- `member_deliberation.md` must NOT contain: `{{ member_name }}`, `{{ persona }}`, `{{ primary_lens }}`, `{{ role_type }}`, `{{ prior_responses }}`

Tech stack: Jinja2 markdown templates.

## Steps
1. Read `templates/member_deliberation.md` in full to understand the current structure.
2. Write `templates/member_system.md` with the persona + goal system prompt content.
3. Rewrite `templates/member_deliberation.md` as the user-turn content (conversation history + chunks + query).
4. Verify both templates render correctly with Jinja2.

## Verification
- File `templates/member_system.md` exists
- `grep -n "member_name\|persona\|primary_lens\|role_type\|goal_name\|goal_description" templates/member_system.md` returns matches for all six variables
- `grep -n "prior_responses\|Prior Council" templates/member_deliberation.md` returns no matches
- `grep -n "member_name\|persona\|primary_lens\|role_type" templates/member_deliberation.md` returns no matches
- `grep -n "conversation_history\|corpus_chunks\|user_message" templates/member_deliberation.md` returns matches for all three variables
- Dynamic: `uv run python -c "import jinja2; e=jinja2.Environment(loader=jinja2.FileSystemLoader('templates')); t=e.get_template('member_system.md'); out=t.render(member_name='X',persona='P',primary_lens='L',role_type='R',goal_name='G',goal_description='D'); assert 'X' in out and 'P' in out, out; print('member_system OK')"` exits 0
- Dynamic: `uv run python -c "import jinja2; e=jinja2.Environment(loader=jinja2.FileSystemLoader('templates')); t=e.get_template('member_deliberation.md'); out=t.render(conversation_history='H',corpus_chunks='C',user_message='Q'); assert 'H' in out and 'C' in out and 'Q' in out, out; print('member_deliberation OK')"` exits 0
- Global Constraint — No inline prompt strings: no Python source files changed in this task
- Global Constraint — `"sequential"` absent: no new occurrences introduced

## Done When
- [ ] `templates/member_system.md` exists with all six variables
- [ ] `templates/member_deliberation.md` contains only `conversation_history`, `corpus_chunks`, `user_message`
- [ ] Both templates render without Jinja2 errors

## Save Command
```
git add templates/member_system.md templates/member_deliberation.md && git commit -m "task-00001: create member_system.md and restructure member_deliberation.md for system/user split"
```
