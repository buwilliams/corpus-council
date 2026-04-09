# Plan: Goals

## Summary
The goals model replaces the hardcoded collection/conversation distinction with a file-driven configuration system. The decomposition follows a foundation-first order: config extension, core module, goal file authoring, CLI update, API update, unit tests, integration tests, documentation, and a final validation pass. Nine tasks total cover all deliverables from project.md.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Add goals_dir, personas_dir, and goals_manifest_path to AppConfig |
| 00001 | programmer | Implement src/corpus_council/core/goals.py |
| 00002 | product-manager | Author goals/intake.md and goals/create-plan.md |
| 00003 | programmer | Update CLI — goals process subcommand and query --goal flag |
| 00004 | api-designer | Update FastAPI API — POST /query endpoint with goal field |
| 00005 | tester | Write unit tests for goals.py |
| 00006 | tester | Write integration tests for goals pipeline and API |
| 00007 | product-manager | Add goal authoring guide documentation |
| 00008 | product-manager | Final validation — verify all deliverables from project.md |

## Dependency Notes
- **00000** must come first: all other tasks depend on `AppConfig` having `goals_dir`, `personas_dir`, and `goals_manifest_path`.
- **00001** depends on 00000 (uses `AppConfig` fields). All subsequent tasks depend on `goals.py` existing.
- **00002** depends on 00001 (goal files must be parseable by `parse_goal_file`). Logically depends on knowing the schema, which 00001 establishes.
- **00003** depends on 00001 (imports `process_goals`, `load_goal`) and 00002 (goal files needed for dynamic verification).
- **00004** depends on 00001 (imports `load_goal`) and 00003 (imports `load_council_for_goal` from updated `council.py`). Also updates `test_api.py` so it depends on the test infrastructure changes in 00000.
- **00005** depends on 00001 (tests `goals.py`) and 00000 (tests new config fields).
- **00006** depends on 00003 and 00004 (tests the full CLI and API pipeline). Must come after goal files (00002) exist.
- **00007** depends on 00001 (adds docstring to `goals.py`) and 00002 (references example goal files).
- **00008** depends on all previous tasks — it is the final validation gate.

**Critical path**: 00000 → 00001 → 00003 → 00004 → 00006 → 00008

## Coverage
| project.md Section | Tasks |
|---|---|
| Goal file format: documented markdown schema | 00001 (code), 00007 (docs) |
| `corpus-council goals process` CLI command | 00003 |
| `goals_manifest.json` produced by process step | 00001, 00003 |
| Updated query CLI and API with `--goal <name>` | 00003, 00004 |
| `goals/intake.md` | 00002 |
| `goals/create-plan.md` | 00002 |
| Removal of hardcoded collection/conversation distinction | 00003, 00004 |
| Documentation update: goal authoring guide | 00007 |
| Unit tests: goal file parsing, manifest generation, goal-not-found | 00005 |
| Integration tests: end-to-end query using real goal files | 00006 |
| `AppConfig` goals fields | 00000 |
| Path traversal prevention | 00001, 00005 (test), 00008 (verify) |
| Idempotency of goals process | 00001 (impl), 00005 (test), 00008 (verify) |
| `--mode` flag continues to work | 00003, 00004, 00008 (verify) |
| Final validation of all deliverables | 00008 |
