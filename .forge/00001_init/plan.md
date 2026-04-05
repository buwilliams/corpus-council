# Plan: Init — Corpus Council Full Implementation

## Summary
The project is decomposed into 23 tasks (00000–00022) organized in strict bottom-up order: infrastructure and scaffolding first, then core modules in dependency order (config → store → corpus → embeddings → council → llm → templates → validation → deliberation → conversation → collection), followed by the API and CLI layers, then the full test suite (fixtures → unit tests → integration tests), and finally an end-to-end validation task. Every task is self-contained and depends only on tasks with lower numbers. The test suite exclusively uses real files, real ChromaDB, and real templates — no mocks for file I/O, FileStore, corpus loading, or ChromaDB as required by project.md.

## Task List

| Task | Role | Title |
|---|---|---|
| 00000 | programmer | Ensure .gitignore covers secrets and build artifacts |
| 00001 | programmer | Project scaffolding — pyproject.toml, directory layout, and config.yaml |
| 00002 | programmer | Implement config.py — config.yaml loader with typed dataclass |
| 00003 | data-engineer | Implement store.py — FileStore with fcntl locking and 2-level directory sharding |
| 00004 | programmer | Implement corpus.py — flat-file corpus ingestion and chunking |
| 00005 | data-engineer | Implement embeddings.py and retrieval.py — ChromaDB embedding pipeline and semantic search |
| 00006 | programmer | Implement council.py — persona loader and CouncilMember type |
| 00007 | programmer | Implement llm.py — LLM client with markdown template rendering |
| 00008 | programmer | Create prompt templates in templates/ |
| 00009 | security-engineer | Implement validation.py — input sanitization for user_id, session_id, plan_id |
| 00010 | programmer | Implement deliberation.py — council deliberation engine with escalation handling |
| 00011 | programmer | Implement conversation.py — conversation mode orchestration |
| 00012 | programmer | Implement collection.py — structured collection mode orchestration |
| 00013 | api-designer | Implement FastAPI Pydantic models in api/models.py |
| 00014 | api-designer | Implement FastAPI app, routers, and exception handlers |
| 00015 | api-designer | Implement Typer CLI with all five commands |
| 00016 | tester | Create test fixtures — conftest.py with real corpus, council, and plan files |
| 00017 | tester | Unit tests — config, store, and corpus modules |
| 00018 | tester | Unit tests — council, llm, and deliberation modules |
| 00019 | tester | Unit tests — conversation and collection modules |
| 00020 | tester | Integration tests — all six FastAPI API endpoints |
| 00021 | tester | Integration tests — full conversation and collection flows |
| 00022 | product-manager | End-to-end validation — coverage, quality gates, and smoke test |

## Dependency Notes

**Critical path (longest chain):**
00000 → 00001 → 00002 → 00003 → 00004 → 00005 → 00006 → 00007 → 00008 → 00009 → 00010 → 00011 → 00012 → 00013 → 00014 → 00015 → 00016 → 00017 → 00018 → 00019 → 00020 → 00021 → 00022

**Key unlock points:**
- 00001 (scaffold) unlocks all module work
- 00002 (config) is imported by every subsequent core module
- 00003 (FileStore) is imported by conversation, collection, and API layers
- 00007 (LLMClient) + 00008 (templates) together unlock deliberation testing
- 00010 (deliberation) unlocks both conversation and collection modes
- 00016 (conftest fixtures) unlocks all test files

**Notable ordering:**
- 00009 (validation) must come before 00014 (API routers) since routers call `validate_id`
- 00008 (templates) must come before 00018 (deliberation tests) since test fixtures reference real template files
- 00005 (embeddings/retrieval) updates `AppConfig` (adds `chroma_collection` field) — this change must be made before any subsequent module that imports `AppConfig`
- 00016 (conftest) must come before 00017–00021 (all test tasks)

## Coverage

| Project.md Section | Tasks |
|---|---|
| Python package, pyproject.toml, uv | 00001 |
| config.yaml, AppConfig | 00001, 00002 |
| Flat-file corpus ingestion | 00004 |
| Embedding pipeline (ChromaDB, sentence-transformers) | 00005 |
| Council loader, CouncilMember | 00006 |
| Council deliberation engine, escalation handling | 00010 |
| Conversation mode | 00011 |
| Collection mode | 00012 |
| User-scoped flat-file store, fcntl locking, 2-level sharding | 00003 |
| Per-user conversation persistence | 00003, 00011 |
| Per-user collection session persistence | 00003, 00012 |
| LLM client, markdown template rendering | 00007, 00008 |
| FastAPI app + 6 endpoints | 00013, 00014 |
| Typer CLI + 5 commands | 00015 |
| Input validation, path sanitization | 00009 |
| .gitignore, secrets hygiene | 00000 |
| Unit tests: all core/ modules | 00017, 00018, 00019 |
| Integration tests: API endpoints | 00020 |
| Integration tests: full conversation + collection flows | 00021 |
| End-to-end validation, coverage gate | 00022 |
