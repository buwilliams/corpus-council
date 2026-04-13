# Task 00001: Update Prompt Templates

## Role
prompt-engineer

## Objective
Remove all deliberation-structure leakage from four user-facing prompt templates. After these changes, no template text that appears in an LLM response could reveal to a user that a multi-member council reviewed their query. Position-1 must be the single authoritative voice in all templates.

## Context

**Files to modify:**
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/member_deliberation.md`
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/final_synthesis.md`
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_resolution.md`
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/evaluator_consolidated.md`

**Files that must NOT be modified:**
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/council_consolidated.md`
- `/home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_check.md`

**Current state of each template:**

`member_deliberation.md` — ends with:
```
Your response will be synthesized with other council members' independent responses by the position-1 authority member.
```
This tells members they are part of a multi-member synthesis, priming them to write as committee contributors.

`final_synthesis.md` — contains:
- Section header: `## Independent Member Responses`
- Introduction line: `The following are the independent responses from all council members during deliberation:`
- Instruction: `Resolve any disagreements or tensions between council members`

`escalation_resolution.md` — contains:
- `An escalation was triggered during deliberation. Details:`
- Section header: `## Independent Member Responses`
- Introduction line: `The following responses were collected before the escalation:`
- Instruction: `Incorporate the relevant member response context`

`evaluator_consolidated.md` — contains:
- Opening preamble: `You are the evaluator responsible for synthesizing the council's consolidated responses into a single, authoritative final answer for the user.`
- Section header: `## Council Responses`
- Introduction line: `The following are the responses from all council members:`
- Instruction: `Integrate the strongest and most relevant insights from all council members`
- Instruction: `Resolve any tensions or disagreements between members`

**How these templates are used in the codebase:**

`member_deliberation.md` — called once per non-position-1 member in the parallel path (`deliberation.py`), with system prompt from `member_system.md`. No change needed to Jinja2 variables; only the instruction text changes.

`final_synthesis.md` — called by position-1 in the parallel path when no escalation occurs (`deliberation.py`). Receives `{{ member_responses }}` which after Task 00002 will contain anonymous `Perspective N:` headers. Rename the section to match.

`escalation_resolution.md` — called by position-1 in the parallel path when escalation occurs (`deliberation.py`). Receives `{{ member_responses }}` and `{{ escalation_flags }}`. After Task 00002, both will be anonymized. Rename and reframe accordingly.

`evaluator_consolidated.md` — called in the consolidated path (`consolidated.py`). Receives `{{ user_message }}`, `{{ council_responses }}` (the raw `council_consolidated.md` output — this variable name is unchanged), and `{{ escalation_summary }}`. After Task 00002, it will also receive a `system_prompt` from position-1's persona. The template itself must not establish an evaluator/synthesizer role identity since the system prompt does that. The `council_responses` variable name is unchanged (it carries the structured output from `council_consolidated.md`).

## Steps

1. **Read all four templates** in full before making any change.

2. **Update `member_deliberation.md`**:
   - Remove the single sentence: `Your response will be synthesized with other council members' independent responses by the position-1 authority member.`
   - Do not change anything else — the persona framing, query presentation, corpus context, and `Respond now:` line must remain exactly as-is.

3. **Update `final_synthesis.md`**:
   - Rename `## Independent Member Responses` to `## Internal Analysis`.
   - Remove the line `The following are the independent responses from all council members during deliberation:` (the `{{ member_responses }}` variable that follows should remain, just with the preamble sentence removed).
   - In the `## Instructions` bullet list, replace `Resolve any disagreements or tensions between council members` with `Speak in your own voice drawing on the internal analysis above`.
   - Remove the phrase "and the independent member responses above" from the synthesis opening sentence (or rephrase so it does not reference "member responses" — the variable is present in the template but the instructions must not describe it as coming from "council members").
   - Ensure no remaining occurrence of: "council member", "deliberation", "resolve disagreements", "member responses" (in instruction text — the Jinja2 variable `{{ member_responses }}` must remain in the data section).

4. **Update `escalation_resolution.md`**:
   - In `## Escalation Flags`, replace `An escalation was triggered during deliberation. Details:` with `A critical concern was identified that requires direct attention before responding:`.
   - Rename `## Independent Member Responses` to `## Internal Analysis`.
   - Remove the line `The following responses were collected before the escalation:`.
   - In `## Instructions`, replace `An escalation has occurred that requires your attention before a final response can be given. Drawing on the corpus material, the escalation flags, and the independent member responses collected so far, provide a resolution.` with `A critical concern requires your direct attention before responding. Drawing on the corpus material, the concern details, and the internal analysis above, provide your response.`
   - In the bullet list: replace `Incorporate the relevant member response context` with `Draw on the internal analysis above where relevant`.
   - Ensure no remaining occurrence of: "escalation was triggered during deliberation", "Independent Member Responses", "member response context".

5. **Update `evaluator_consolidated.md`**:
   - Remove the opening preamble paragraph: `You are the evaluator responsible for synthesizing the council's consolidated responses into a single, authoritative final answer for the user.` (remove the entire paragraph including the blank line that follows it).
   - Rename `## Council Responses` to `## Internal Analysis`.
   - Remove the line `The following are the responses from all council members:`.
   - In `## Instructions`, replace the current synthesis framing with instructions for position-1 to compose its own authoritative response. The new instruction paragraph should read: `Compose your response to the user's message. Your response should:`.
   - Replace the bullet `Integrate the strongest and most relevant insights from all council members` with `Draw on the strongest and most relevant insights from the internal analysis above`.
   - Replace the bullet `Resolve any tensions or disagreements between members` with `Provide a clear, well-grounded, and direct answer`.
   - Keep `Address any escalation concerns raised (if any)` if present in the escalation block — or equivalent, so long as it does not reference "council members" or "members."
   - Ensure no remaining occurrence of: "council members", "evaluator", "synthesizing", "tensions or disagreements between members".

6. **Verify no leakage remains** in the four modified templates:
   ```
   grep -i "council member\|deliberation\|synthesize.*member\|resolve disagreement\|Independent Member\|evaluator.*council\|tensions.*member\|synthesized with other" /home/buddy/projects/corpus-council/src/corpus_council/templates/member_deliberation.md /home/buddy/projects/corpus-council/src/corpus_council/templates/final_synthesis.md /home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_resolution.md /home/buddy/projects/corpus-council/src/corpus_council/templates/evaluator_consolidated.md
   ```
   This must return no matches.

7. **Confirm protected templates are untouched** — do not modify these files at all:
   - `/home/buddy/projects/corpus-council/src/corpus_council/templates/council_consolidated.md`
   - `/home/buddy/projects/corpus-council/src/corpus_council/templates/escalation_check.md`

8. **Run verification**:
   ```
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```
   All must exit 0. Template changes do not affect linting or type checking, but template rendering is exercised by tests — confirm no test fails due to missing Jinja2 variables or template syntax errors.

## Verification

- `grep -i "council member\|deliberation\|synthesize.*member\|resolve disagreement\|Independent Member\|evaluator.*council\|tensions.*member\|synthesized with other"` on the four modified templates returns no matches.
- `member_deliberation.md`: the sentence about synthesis with other council members is absent; the `Respond now:` line and all variable placeholders are intact.
- `final_synthesis.md`: section is titled `## Internal Analysis`; instructions say "speak in your own voice drawing on internal analysis"; no "council member" or "deliberation" language in instruction text.
- `escalation_resolution.md`: no "escalation was triggered during deliberation" phrase; section is titled `## Internal Analysis`; position-1 voice framing throughout instructions.
- `evaluator_consolidated.md`: no evaluator/synthesizer preamble; section is titled `## Internal Analysis`; instructions frame position-1 composing its own response.
- `council_consolidated.md` and `escalation_check.md` are byte-for-byte unchanged.
- `uv run pytest` exits 0.
- `uv run mypy src/` exits 0.
- `uv run ruff check src/` exits 0.

## Done When
- [ ] `member_deliberation.md`: synthesis-disclosure sentence removed; all Jinja2 variables intact.
- [ ] `final_synthesis.md`: `## Internal Analysis` section header; "council member", "deliberation", "resolve disagreements between members" absent from instruction text.
- [ ] `escalation_resolution.md`: "escalation was triggered during deliberation" absent; `## Internal Analysis` section header; position-1 voice framing.
- [ ] `evaluator_consolidated.md`: evaluator/synthesizer preamble removed; `## Internal Analysis` section header; "council members" and "tensions or disagreements between members" absent.
- [ ] `council_consolidated.md` unchanged.
- [ ] `escalation_check.md` unchanged.
- [ ] `uv run pytest` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run ruff check src/` exits 0.

## Save Command
```
git add src/corpus_council/templates/member_deliberation.md src/corpus_council/templates/final_synthesis.md src/corpus_council/templates/escalation_resolution.md src/corpus_council/templates/evaluator_consolidated.md && git commit -m "task-00001: update prompt templates for single-persona framing"
```
