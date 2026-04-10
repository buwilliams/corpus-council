# Plan: Goals Unification

## Summary
The project corrects the architectural misalignment between the goals model and the REST API, CLI, and frontend UI. The decomposition proceeds bottom-up: data layer first (FileStore path helpers), then core logic (run_goal_chat), then API surface (models, router, app.py), then CLI, then frontend, then tests. Seven tasks total (00000–00006) — no gitignore task needed because the existing .gitignore already covers all required entries.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Add FileStore goal path helpers |
| 00001 | programmer | Implement core/chat.py with run_goal_chat |
| 00002 | programmer | Update models.py — add ChatRequest/ChatResponse, remove obsolete models |
| 00003 | programmer | Create chat router, update app.py, delete old routers |
| 00004 | programmer | Update CLI — chat --goal, remove query and collect |
| 00005 | programmer | Update frontend — 3-tab Goals/Files/Admin layout |
| 00006 | tester | Update tests — integration tests for POST /chat, remove old endpoint tests |

## Dependency Notes

- **00000** is a pure addition with no dependencies — safe to start immediately.
- **00001** depends on 00000 (uses `goal_messages_path` and `goal_context_path`).
- **00002** has no code dependencies (models.py is standalone) but must precede 00003 (chat router imports ChatRequest/ChatResponse).
- **00003** depends on 00001 (imports `run_goal_chat`) and 00002 (imports `ChatRequest`/`ChatResponse`).
- **00004** depends on 00001 (imports `run_goal_chat`). It also benefits from 00003 completing (old router imports gone), but the CLI file itself does not import the API routers.
- **00005** depends on 00003 (the `POST /chat` endpoint must exist for dynamic verification).
- **00006** depends on all prior tasks (tests the full integrated system).

**Critical path:** 00000 → 00001 → 00003 → 00006

## Coverage

| project.md Section | Tasks |
|---|---|
| Core: FileStore path helpers | 00000 |
| Core: run_goal_chat in core/chat.py | 00001 |
| Core: delete core/conversation.py and core/collection.py | 00006 |
| REST API: ChatRequest/ChatResponse Pydantic models | 00002 |
| REST API: POST /chat router (chat.py) | 00003 |
| REST API: remove query/conversation/collection routers and models | 00002, 00003 |
| REST API: register chat router in app.py | 00003 |
| CLI: chat --goal --session --mode | 00004 |
| CLI: remove query and collect commands | 00004 |
| UI: 3-tab Goals/Files/Admin layout | 00005 |
| UI: Goals tab wired to POST /chat | 00005 |
| UI: remove query/conversation/collection JS | 00005 |
| Tests: integration tests for POST /chat | 00006 |
| Tests: unit tests for FileStore path helpers | 00000 |
| Tests: unit tests for run_goal_chat | 00001, 00006 |
| Tests: remove old endpoint tests | 00006 |
