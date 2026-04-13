# Plan: Single Persona

## Summary

This project makes the internal council deliberation machinery fully opaque to users. Position-1 is the only voice users ever experience — no template, no output, and no LLM call may reference "council members," "deliberation," "resolve disagreements," or any other detail that reveals the multi-member architecture. Changes fall into three areas: (1) template edits to remove deliberation-leakage language, (2) Python changes to thread `goal_name`/`goal_description` into the consolidated path and pass position-1's system prompt to the evaluator LLM call, and (3) test updates to cover the new signature and the anonymous response headers.

Work is decomposed into 4 tasks (00001–00004) running in strict dependency order. Template changes (00001) first, Python changes (00002) second, test updates (00003) third, and a final verification pass (00004) last.

## Task List

| Task | Role | Title |
|---|---|---|
| 00001 | prompt-engineer | Update Prompt Templates |
| 00002 | programmer | Update consolidated.py, chat.py, and deliberation.py |
| 00003 | tester | Update Tests |
| 00004 | product-manager | Full Verification Pass |

## Dependency Notes

- **00001** has no code dependencies — template changes are self-contained and must happen first so 00002 can verify the template variable names it needs to pass.
- **00002** depends on 00001 because `evaluator_consolidated.md` template changes determine whether `goal_name`/`goal_description` need to be passed in the evaluator context, and the reframed template must receive a system prompt from position-1's persona.
- **00003** depends on 00002 because the tests cover the new `run_consolidated_deliberation()` signature and the `_format_member_responses()` anonymous headers, both of which are introduced in 00002.
- **00004** depends on 00001–00003 being complete — it runs all three quality gates and verifies every deliverable.

**Critical path**: 00001 → 00002 → 00003 → 00004

## Coverage

| project.md Deliverable | Covered By |
|---|---|
| `member_deliberation.md`: remove synthesis-disclosure sentence | Task 00001 |
| `final_synthesis.md`: rename section, reframe instructions | Task 00001 |
| `escalation_resolution.md`: remove deliberation framing, reframe as position-1 | Task 00001 |
| `evaluator_consolidated.md`: remove evaluator preamble, rename section, reframe | Task 00001 |
| `consolidated.py`: `goal_name`/`goal_description` params, position-1 system prompt | Task 00002 |
| `chat.py`: pass `goal_name`/`goal_description` to `run_consolidated_deliberation()` | Task 00002 |
| `deliberation.py`: anonymous `Perspective N:` headers, no member names in escalation flags | Task 00002 |
| `test_consolidated.py`: new params, system prompt assertion | Task 00003 |
| `test_deliberation.py`: `_format_member_responses` no-member-name assertion | Task 00003 |
| Full suite green: ruff, mypy, pytest | Task 00004 |
