# Plan: Externalized Users

## Summary
This project eliminates five separate path config keys (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`) in favor of a single `data_dir` with conventional subdirectories derived by convention. The work is decomposed into 8 tasks (00000–00007): constitution update first, then config/code changes, then test updates, then config YAML and README, and finally a full verification pass. Each task is self-contained and depends only on lower-numbered tasks.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Update Constitution |
| 00001 | programmer | Simplify AppConfig and load_config |
| 00002 | data-engineer | Update FileStore to Accept users_dir as Base |
| 00003 | tester | Update conftest.py and Existing Tests |
| 00004 | tester | Write New Config and Store Tests |
| 00005 | programmer | Update config.yaml |
| 00006 | programmer | Update README.md |
| 00007 | programmer | Full Verification Pass |

## Dependency Notes

- **00000** has no code dependencies — constitution must be first per spec.
- **00001** depends on 00000 conceptually (constitution authorizes the change) and must be done before any test or YAML changes.
- **00002** depends on 00001 because it uses `config.users_dir` (the new property added in 00001).
- **00003** depends on 00001 and 00002 because `conftest.py` constructs `AppConfig` and `FileStore`, both of which change in those tasks.
- **00004** depends on 00003 because it appends new tests to files updated by 00003 and needs the full suite green before adding more.
- **00005** depends on 00001 because the deprecated keys now cause `ValueError` if present — removing them from config.yaml makes the startup-time `load_config()` call in `app.py` succeed.
- **00006** depends on 00001 and 00005 because it documents the new config model.
- **00007** is the gate task — depends on all prior tasks being complete and exits 0 on all three quality checks.

**Critical path**: 00000 → 00001 → 00002 → 00003 → 00004 → 00005 → 00006 → 00007

## Coverage

| project.md Deliverable | Covered By |
|---|---|
| `constitution.md` updated | Task 00000 |
| `AppConfig` simplified (remove fields, add `@property`) | Task 00001 |
| `load_config()` migration errors for deprecated keys | Task 00001 |
| `ingest_corpus()` updated to accept optional `corpus_dir` | Task 00001 |
| `dataclasses.replace` callsites removed | Task 00001 |
| `FileStore` updated to use `users_dir` as base | Task 00002 |
| All `FileStore(config.data_dir)` callsites updated | Task 00002 |
| `conftest.py` updated to use simplified `AppConfig` | Task 00003 |
| Existing tests updated for new behavior | Task 00003 |
| New unit tests: migration errors (5 keys) | Task 00004 |
| New unit tests: all 8 derived `@property` paths | Task 00004 |
| New unit tests: `FileStore` initialized with `users_dir` | Task 00004 |
| `config.yaml` updated (deprecated keys removed, layout documented) | Task 00005 |
| `README.md` updated (simplified config ref, migration note) | Task 00006 |
| Full suite green: ruff, mypy, pytest | Task 00007 |
