# Plan: Sequential → Parallel Deliberation

## Summary

The project replaces the sequential deliberation mode with a parallel mode and introduces a system/user prompt split: each council member's persona + goal is sent as the Anthropic system prompt, while conversation history + corpus chunks + user query form the user-turn message. The decomposition produces 8 tasks: 1 LLM layer update, 2 template updates, 1 core rewrite, 1 config rename, 1 API/CLI update, 1 README update, and 1 test overhaul.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Update LLMClient to Support Separate System Prompt |
| 00001 | programmer | Create member_system.md and Restructure member_deliberation.md |
| 00002 | programmer | Update final_synthesis.md and escalation_resolution.md Templates |
| 00003 | concurrency-engineer | Rewrite deliberation.py — Parallel Mode with ThreadPoolExecutor |
| 00004 | programmer | Rename sequential → parallel in config.yaml, config.py, and chat.py |
| 00005 | api-designer | Update API Models and CLI — mode Field and --mode Flag |
| 00006 | product-manager | Update README.md Deliberation Modes Documentation |
| 00007 | tester | Update Existing Tests and Write New Parallel Deliberation Tests |

## Dependency Notes

- **00000 must precede 00003**: `deliberation.py` calls `llm.call(..., system_prompt=...)`. The parameter must exist before the call site is written.
- **00001 and 00002 must precede 00003**: The rewritten `deliberation.py` passes context dicts using new variable names (`member_responses`, `conversation_history`, `goal_description`). Templates must match before the call sites reference them.
- **00003 must precede 00007**: Tests verify the new parallel behavior, system prompt content, and conversation history threading. These cannot be written until `deliberation.py` establishes the new contracts.
- **00004 must precede 00007**: Integration test fixture uses `deliberation_mode: "sequential"` which must be updated after config validation rejects it.
- **00005 must precede 00007**: Test for `mode: "sequential"` → 422 only holds after the `Literal` type is applied.
- **00001 and 00002 can run in any order** relative to each other.
- **00004 and 00005 can run in any order** relative to each other.
- **00006 (README) has no code dependencies** and can run at any point.
- **Critical path**: 00000 → 00001 → 00003 → 00004 → 00007.

## Coverage

| project.md Deliverable | Tasks |
|---|---|
| `llm.py` updated — `system_prompt` parameter added | 00000 |
| New template `member_system.md` — persona + goal system prompt | 00001 |
| `member_deliberation.md` restructured — user turn: history + chunks + query | 00001 |
| `final_synthesis.md` updated — persona removed, history added, `member_responses` | 00002 |
| `escalation_resolution.md` updated — persona removed, history added | 00002 |
| `deliberation.py` rewritten — parallel `ThreadPoolExecutor`, system/user split, history + goal threading | 00003 |
| `chat.py` updated — passes `conversation_history`, `goal_name`, `goal_description` | 00003 |
| Escalation — flags collected post-flight, position-1 resolves in synthesis | 00003 |
| Mode name `sequential` → `parallel` in `config.yaml`, `config.py`, `chat.py` | 00004 |
| Mode name `sequential` → `parallel` in API `mode` field | 00005 |
| Mode name `sequential` → `parallel` in CLI `--mode` flag | 00005 |
| `README.md` deliberation modes table updated | 00006 |
| All existing tests updated; new parallel, system prompt, and history tests | 00007 |
