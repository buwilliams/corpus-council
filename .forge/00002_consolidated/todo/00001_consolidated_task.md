# Task 00001: Create council_consolidated.md and evaluator_consolidated.md Jinja2 templates

## Role
programmer

## Objective
Create two new Jinja2 template files in `templates/`:
1. `templates/council_consolidated.md` — receives `members`, `user_message`, `corpus_chunks`; produces one clearly delimited response block per member, each ending with an `ESCALATION:` line
2. `templates/evaluator_consolidated.md` — receives `user_message`, `council_responses`, `escalation_summary`; synthesizes a final answer and resolves any escalation concerns

Both templates must be valid Jinja2 (no Python string formatting), must never embed hardcoded persona descriptions or behavioral rules, and must produce output that the parser in `consolidated.py` (Task 00002) can reliably split per member.

## Context

**Template system:** `LLMClient.render_template(template_name, context)` in `src/corpus_council/core/llm.py` uses `jinja2.Environment(loader=jinja2.FileSystemLoader(...))`. Template files live in `templates/` at the project root. The `.md` extension is appended automatically if absent when calling `llm.call(template_name, context)`.

**Existing templates for reference** (do not modify):
- `templates/member_deliberation.md` — uses `{{ member_name }}`, `{{ persona }}`, `{{ user_message }}`, etc.
- `templates/escalation_check.md` — uses `{{ escalation_rule }}`, `{{ member_response }}`
- `templates/final_synthesis.md` — uses `{{ member_name }}`, `{{ user_message }}`, `{{ deliberation_log }}`
- `templates/escalation_resolution.md` — uses `{{ user_message }}`, `{{ escalation_log }}`, `{{ prior_responses }}`

**Template variables for `council_consolidated.md`:**
- `members` — a Python list of `CouncilMember` dataclass instances. Each has attributes: `name` (str), `persona` (str), `primary_lens` (str), `role_type` (str), `escalation_rule` (str), `body` (str). Iterate with `{% for member in members %}`.
- `user_message` — str
- `corpus_chunks` — str (already formatted by `_format_chunks()` before being passed to `llm.call()`)

**Template variables for `evaluator_consolidated.md`:**
- `user_message` — str
- `council_responses` — str (the raw output of the council call, containing all member blocks)
- `escalation_summary` — str (concatenated `ESCALATION:` lines that were not `NONE`; may be empty string)

**Parser contract (used by `consolidated.py` in Task 00002):**

The council template must produce blocks that the parser can split reliably. Use this delimiter structure so `consolidated.py` can split on `=== MEMBER:`:

```
=== MEMBER: {member.name} ===
...member's response...
ESCALATION: NONE
=== END MEMBER ===
```

Each member block must end with exactly one `ESCALATION:` line containing either `NONE` or a brief concern. The parser in `consolidated.py` will:
1. Split council output on `=== MEMBER:` to get per-member blocks
2. Extract the `ESCALATION:` line from each block
3. Build `escalation_summary` from non-`NONE` escalation lines

**Global constraints:**
- No Python string literals may be used as prompts — every prompt goes through a Jinja2 template file
- No hardcoded personas or escalation rules in the template — the template receives them via `members` variable from the council directory
- No new Python packages required — Jinja2 is already installed

## Steps

1. Create `templates/council_consolidated.md` with:
   - A system instruction preamble explaining the task (no hardcoded behavioral content)
   - A `{% for member in members %}` loop that renders one block per member with the delimiter structure described above
   - Each block instructs the LLM to respond as that member using their `persona`, `primary_lens`, `role_type`, and `escalation_rule`, then end with `ESCALATION: NONE` or `ESCALATION: <concern>`
   - The `user_message` and `corpus_chunks` sections are included once (not per-member)

2. Create `templates/evaluator_consolidated.md` with:
   - An instruction to synthesize a final response from the council member responses
   - A section for `{{ council_responses }}` (the full council output)
   - A section for `{{ escalation_summary }}` with conditional display (show only if non-empty)
   - An instruction to resolve any escalation concerns that appear in the escalation summary
   - The original `{{ user_message }}` for reference

3. Verify both templates render without Jinja2 errors using a quick Python check (see Verification).

## Verification

- Structural:
  - File `templates/council_consolidated.md` exists
  - File `templates/evaluator_consolidated.md` exists
  - `grep -n '{%' /home/buddy/projects/corpus-council/templates/council_consolidated.md` shows at least one Jinja2 control block (`{% for %}`/`{% endfor %}`)
  - `grep -n 'ESCALATION:' /home/buddy/projects/corpus-council/templates/council_consolidated.md` shows the escalation line pattern
  - `grep -n 'council_responses\|escalation_summary' /home/buddy/projects/corpus-council/templates/evaluator_consolidated.md` shows both variables used
  - `grep -n '=== MEMBER:' /home/buddy/projects/corpus-council/templates/council_consolidated.md` shows the delimiter used in the template
- Global constraint — no inline prompt strings in Python:
  - `grep -rn 'f".*\{.*\}' /home/buddy/projects/corpus-council/templates/` should not return Python f-strings (templates use Jinja2 `{{ }}` syntax, not Python `{ }`)
  - `grep -rn 'hardcoded\|persona.*=\s*"' /home/buddy/projects/corpus-council/templates/council_consolidated.md` returns no matches (no hardcoded persona strings)
- Dynamic: render both templates with sample data and verify output contains expected content:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run python -c "
  import jinja2, pathlib

  templates_dir = pathlib.Path('templates')
  env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(templates_dir)), autoescape=False)

  # Test council_consolidated.md
  tmpl = env.get_template('council_consolidated.md')
  members_data = [
      type('M', (), {'name': 'Alice', 'persona': 'Analyst', 'primary_lens': 'accuracy', 'role_type': 'critic', 'escalation_rule': 'Halt if false', 'body': ''})(),
      type('M', (), {'name': 'Bob', 'persona': 'Synthesizer', 'primary_lens': 'balance', 'role_type': 'synthesizer', 'escalation_rule': 'Halt if incomplete', 'body': ''})(),
  ]
  out = tmpl.render(members=members_data, user_message='What is AI?', corpus_chunks='AI is a field of study.')
  assert 'Alice' in out, 'Alice not in council output'
  assert 'Bob' in out, 'Bob not in council output'
  assert 'ESCALATION:' in out, 'ESCALATION: not in council output'
  print('council_consolidated.md OK')

  # Test evaluator_consolidated.md
  tmpl2 = env.get_template('evaluator_consolidated.md')
  out2 = tmpl2.render(user_message='What is AI?', council_responses='=== MEMBER: Alice ===\nAI is...\nESCALATION: NONE\n=== END MEMBER ===', escalation_summary='')
  assert 'council_responses' not in out2 or '=== MEMBER: Alice ===' in out2, 'council_responses not rendered'
  print('evaluator_consolidated.md OK')
  "
  ```

## Done When
- [ ] `templates/council_consolidated.md` exists and uses Jinja2 loop over `members`, includes `user_message` and `corpus_chunks`, produces `=== MEMBER: <name> ===` delimited blocks each ending with `ESCALATION:`
- [ ] `templates/evaluator_consolidated.md` exists and uses `{{ council_responses }}`, `{{ escalation_summary }}`, and `{{ user_message }}`
- [ ] Both templates render without Jinja2 errors with sample data
- [ ] No hardcoded persona descriptions or escalation rules appear in either template
- [ ] All verification checks pass

## Save Command
```
git add templates/council_consolidated.md templates/evaluator_consolidated.md && git commit -m "task-00001: add council_consolidated.md and evaluator_consolidated.md Jinja2 templates"
```
