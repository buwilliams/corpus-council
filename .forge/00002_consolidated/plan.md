# Plan: Consolidated — Two-Call Deliberation Mode

## Summary

The project adds a `consolidated` deliberation mode that reduces N-member council queries from `2N+1` sequential LLM calls to exactly 2. The decomposition follows a strict bottom-up order: config extension first, then templates, then the core implementation, then dispatch wiring in conversation/collection layers, then the API and CLI surfaces, then unit tests, then integration tests, and finally a validation-only sign-off task. Nine tasks total (00000–00008).

The `.gitignore` already covers all required entries (`.env`, `*.key`, `__pycache__/`, `dist/`, `build/`, etc.), so no gitignore task is needed and numbering starts at 00000 for the first real work task.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Extend AppConfig with deliberation_mode and update config.yaml |
| 00001 | programmer | Create council_consolidated.md and evaluator_consolidated.md Jinja2 templates |
| 00002 | programmer | Implement run_consolidated_deliberation() in consolidated.py |
| 00003 | programmer | Add mode dispatch to conversation.py and collection.py |
| 00004 | programmer | Add mode field to API models and update routers |
| 00005 | programmer | Add --mode flag to chat, query, and collect CLI commands |
| 00006 | tester | Write unit tests for consolidated.py |
| 00007 | tester | Write integration tests for the consolidated path |
| 00008 | product-manager | Final verification — run full dynamic verification suite |

## Dependency Notes

- **00001 depends on 00000**: templates reference `members` from council directory, but the config loading for `deliberation_mode` is needed for downstream tasks.
- **00002 depends on 00001**: `consolidated.py` calls `llm.call("council_consolidated", ...)` and `llm.call("evaluator_consolidated", ...)` — the templates must exist for any LLM call to succeed.
- **00003 depends on 00002**: `conversation.py` imports and dispatches to `run_consolidated_deliberation()`.
- **00004 depends on 00000 and 00003**: API routers resolve `config.deliberation_mode` (from 00000) and call `run_conversation(..., mode=...)` (from 00003).
- **00005 depends on 00000 and 00003**: CLI resolves `config.deliberation_mode` and calls updated core functions.
- **00006 depends on 00001 and 00002**: unit tests render the real templates (00001) and call `run_consolidated_deliberation()` (00002).
- **00007 depends on 00003, 00004, 00005, and 00006**: integration tests exercise the full stack end-to-end.
- **00008 depends on all prior tasks**: sign-off only, no code changes.

Critical path: 00000 → 00002 → 00003 → 00004 → 00007 → 00008. Templates (00001) must complete before the consolidated module (00002). CLI (00005) can be done in parallel with 00004 once 00003 is done.

## Coverage

| project.md Section / Feature | Tasks |
|---|---|
| `AppConfig.deliberation_mode` + `config.yaml` key | 00000 |
| `templates/council_consolidated.md` | 00001 |
| `templates/evaluator_consolidated.md` | 00001 |
| `src/corpus_council/core/consolidated.py` — `run_consolidated_deliberation()` | 00002 |
| Deliberation dispatch in `conversation.py` | 00003 |
| `mode` parameter in `start_collection()` / `respond_collection()` | 00003 |
| `mode` field in API request models (Pydantic Literal enum) | 00004 |
| API routers resolve and forward mode | 00004 |
| HTTP 422 for invalid mode | 00004 |
| `--mode` CLI flag on chat, query, collect | 00005 |
| Mode resolution priority (per-request → config → default) | 00004, 00005 |
| Unit tests: template rendering, call count, DeliberationResult return, escalation parsing | 00006 |
| Integration tests: run_conversation consolidated, POST /conversation consolidated, CLI --mode | 00007 |
| API test: POST /conversation invalid mode returns 422 | 00007 |
| Coverage threshold >= 80% on core/ | 00007 |
| Full dynamic verification (ruff, mypy, pytest) | 00008 |
| Sequential path unchanged / no new dependencies | 00008 |
