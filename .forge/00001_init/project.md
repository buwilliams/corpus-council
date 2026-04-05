# Project Spec: Init — Corpus Council Full Implementation

## Goal

A working Corpus Council platform: a Python API and CLI that accepts a flat-file knowledge corpus and a set of markdown-defined council personas, builds and queries vector embeddings for retrieval, and routes every interaction through a hierarchical council deliberation to produce grounded, accurate responses. Both interaction modes — conversation and collection — are fully implemented, tested, and accessible via the API and CLI.

## Why This Matters

This is the entire platform. Without it, nothing else exists. The init spec establishes the architecture every future spec builds on: the corpus pipeline, the council engine, the two interaction modes, and both interfaces. Getting the structure right here — especially the file-driven, configuration-over-code approach — determines how easy or hard it will be to deploy this for any domain.

## Deliverables

- [ ] Python package (`corpus_council`) with `pyproject.toml`, managed by `uv`
- [ ] Flat-file corpus ingestion: reads `.md` and `.txt` files from a `corpus/` directory, chunks them, stores chunk metadata as flat files
- [ ] Embedding pipeline: generates embeddings from corpus chunks using a configurable embedding provider (default: `sentence-transformers`); stores vectors in a local ChromaDB instance
- [ ] Council loader: reads persona markdown files from a `council/` directory; each file follows the standard council member template
- [ ] Council deliberation engine: full pipeline — context load → corpus retrieval → member iteration (position descending) → escalation handling → position-1 final synthesis → persist
- [ ] Conversation mode: runs the full deliberation pipeline for open-ended user messages; history resumable by `user_id`
- [ ] Collection mode: structured interview driven by a markdown collection plan → council validates collected values → session closes when all required fields are collected → returns structured JSON
- [ ] User-scoped flat-file store: all user data persisted under `data/users/{id[0:2]}/{id[2:4]}/{user_id}/` (2-level directory sharding)
- [ ] Per-user conversation persistence: `chat/messages.jsonl` (full turn log: user message + deliberation log + final response) + `chat/context.json`; resumable by `user_id`
- [ ] Per-user collection session persistence: `collection/{session_id}/messages.jsonl`, `collection/{session_id}/collected.json`, `collection/{session_id}/session.json`; caller passes `user_id` + optional `session_id`
- [ ] `FileStore` class: encapsulates all file I/O with fcntl locking for safe concurrent writes
- [ ] LLM client: all calls made via markdown prompt templates in `templates/`; provider and model configurable via `config.yaml`
- [ ] FastAPI app with endpoints: `POST /conversation`, `POST /collection/start`, `POST /collection/respond`, `GET /collection/{user_id}/{session_id}`, `POST /corpus/ingest`, `POST /corpus/embed`
- [ ] Typer CLI with commands: `chat <user_id>`, `collect <user_id> [--session <session_id>]`, `ingest <path>`, `embed`, `serve`
- [ ] Configuration via `config.yaml`: LLM provider + model, embedding provider + model, data directory, corpus/council/template paths
- [ ] Full test suite covering corpus pipeline, council deliberation (including escalation path), both modes, user store resume, and all API endpoints

## Tech Stack

- Language: Python 3.12+
- Runtime / Platform: Local / any server
- Key dependencies: FastAPI, Typer, ChromaDB, sentence-transformers, anthropic SDK, PyYAML, pytest
- Build tool: `uv`
- Package manager: `uv`

## Architecture Overview

### Council Member Template

Every file in `council/` is a markdown file with YAML front matter:

```yaml
---
name: Role label (e.g. "Adversarial Critic")
persona: Who this agent is — their personality, domain, background, and worldview
primary_lens: The dimension they are responsible for judging (e.g. factual accuracy, actionability, ethical implications)
position: Numeric rank — lower is more authoritative; position 1 has final say
role_type: proponent | critic | synthesizer | arbiter | devil's_advocate | domain_specialist
escalation_rule: The core rule that, if violated, halts deliberation
---
```

Body prose below the front matter is passed as additional context to the member's LLM prompt.

### Response Workflow

Every interaction follows this pipeline:

```
User Message
     │
     ▼
Load User Context (chat/context.json or collection/{session_id}/context.json)
     │
     ▼
Embed Message → Query ChromaDB → Top-K Corpus Chunks
     │
     ▼
┌─────────────────────────────────────┐
│         Council Deliberation        │
│                                     │
│  Position N (lowest authority)      │
│    → render prompt + call LLM       │
│    → check escalation_rule          │
│         │ violation?                │
│         ├── yes → flag + skip ahead │
│         └── no  → next member       │
│                                     │
│  Position N-1 ... (repeat)          │
│                                     │
│  Position 1 (highest authority)     │
│    → synthesize or resolve          │
│    → produce final response         │
└─────────────────────────────────────┘
     │
     ▼
Persist: append full turn to messages.jsonl, update context.json
     │
     ▼
Return Response to Caller
```

**Deliberation detail:**
- Members are iterated from highest `position` number to lowest (least authoritative first)
- Each member receives: user message, retrieved chunks, member's own `persona`/`primary_lens`/`role_type`, and all prior member outputs — rendered via that member's markdown prompt template
- If a member's `escalation_rule` is violated: deliberation halts, violation is flagged, remaining members are skipped, and position 1 receives the escalation flag + full context for resolution
- Position 1 always acts last and always produces the final response — whether via normal synthesis or escalation resolution
- The full turn (user message + deliberation log + final response) is appended to `messages.jsonl`

**Escalation path:**
```
Normal:     Member N → Member N-1 → ... → Position 1 (synthesizes)
Escalation: Member N detects violation → skip remaining → Position 1 (resolves)
```

### Directory Layout

```
corpus-council/
  corpus/          # flat file knowledge (.md, .txt)
  council/         # persona markdown files (YAML front matter + prose)
  templates/       # LLM prompt templates (.md)
  plans/           # collection plan markdown files
  data/
    users/
      {shard1}/    # user_id[0:2]
        {shard2}/  # user_id[2:4]
          {user_id}/
            chat/
              messages.jsonl     # full turn log (user msg + deliberation + response)
              context.json       # current conversation state
            collection/
              {session_id}/
                session.json     # metadata (plan, status, created_at)
                messages.jsonl   # full turn log
                collected.json   # accumulated data points
                context.json     # current plan position / state
    embeddings/    # ChromaDB local vector store
  config.yaml
  src/
    corpus_council/
      api/               # FastAPI app and routers
      cli/               # Typer CLI entry points
      core/
        corpus.py        # ingestion and chunking
        embeddings.py    # configurable embed pipeline
        retrieval.py     # semantic search
        council.py       # persona loading, position ordering
        deliberation.py  # deliberation engine + escalation handling
        conversation.py  # conversation mode orchestration
        collection.py    # collection mode orchestration
        store.py         # FileStore: all user data I/O + fcntl locking
        llm.py           # LLM client, template rendering
        config.py        # config.yaml loader
```

## Testing Requirements

- Unit tests: all `core/` modules — corpus chunking, council loading, deliberation engine (normal path and escalation path), `FileStore` read/write, template rendering
- Integration tests: full conversation and collection flows against a real test corpus with real council personas; all API endpoints; user store persistence and resume
- Test framework: pytest
- Coverage threshold: 80% minimum on `core/`
- What must never be mocked: corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB (real test instance), prompt template rendering

## Code Quality

- Linter / static analysis: ruff
- Formatter: ruff format
- Type checking: mypy (strict on `core/`)
- Commands that must exit 0: `ruff check src/`, `ruff format --check src/`, `mypy src/corpus_council/core/`, `pytest`

## Constraints

- No inline prompt strings in Python — every LLM call renders a markdown template from `templates/`
- No hardcoded personas, rules, or domain logic in Python source
- All council members defined as markdown files with YAML front matter using the standard template
- No relational database or message queue — ChromaDB is the only permitted non-flat-file store and only for embeddings; all user/session data is flat files only
- All corpus documents, persona definitions, collection plans, and prompt templates are plain markdown/text files
- `config.yaml` is the only place deployment-specific values are set
- Embedding provider is pluggable via config — `sentence-transformers` is the default
- LLM provider is pluggable via config — Anthropic is the default
- API keys via environment variables only — never in `config.yaml` or source
- `user_id` is always caller-supplied — Corpus Council never generates or validates user identity
- Python throughout; no other backend languages

## Performance Requirements

- Embedding ingestion: index a 500-document corpus in under 60 seconds on a standard laptop
- Conversation response: end-to-end latency (retrieval + deliberation + LLM call) under 10 seconds for a single-turn query with a 3-persona council
- Session file writes: append to `messages.jsonl` and update `context.json` before returning API response

## Security Considerations

- LLM and embedding API keys via environment variables only
- No user auth — the calling platform is responsible
- Corpus and persona files are read-only at runtime
- fcntl file locking on all user data writes to prevent corruption under concurrent access

## Out of Scope

- Frontend or chat UI of any kind
- User authentication, session management, or rate limiting
- Fine-tuning or training models
- Any FTA-specific corpus, personas, or collection plans (deployment artifacts, not platform)
- Multi-tenancy or per-request corpus isolation

## Open Questions

None — all resolved.

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- No inline prompt strings in Python source — every LLM call must render a markdown template from `templates/`; confirmed by grepping `src/` for string literals passed directly to LLM client calls
- No hardcoded behavioral rules, personas, or domain logic in Python source — all such content must live in `council/` markdown files or `config.yaml`
- No relational database or message queue — ChromaDB is the only permitted non-flat-file store and only for embeddings; all user/session data is flat files under `data/users/`
- All LLM and embedding API keys are supplied via environment variables only — never written to `config.yaml`, source files, or committed to the repository
- `ruff check src/` exits 0 with no errors or warnings
- `ruff format --check src/` exits 0 with no formatting violations
- `mypy src/corpus_council/core/` exits 0 with no errors (strict mode)
- No test stubs, mocks, or fakes for corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB, or prompt template rendering — all tests exercise real code paths against real files
- `pytest` exits 0 with all tests passing and at least 80% coverage on `src/corpus_council/core/`
- Python throughout — no non-Python backend languages or build steps

## Dynamic Verification
- **Exercise command:** `uv run python -c "from corpus_council.core.config import load_config; load_config('config.yaml')"` and `uv run corpus-council serve &` then `curl -sf http://localhost:8000/docs > /dev/null`
- **Ready check:** `curl -sf http://localhost:8000/docs > /dev/null`
- **Teardown:** `kill $APP_PID`
- **Environment:** `ANTHROPIC_API_KEY=<key>`

## Execution
- **Test:** `uv run pytest`
- **Typecheck:** `uv run mypy src/corpus_council/core/`
- **Lint:** `uv run ruff check src/ && uv run ruff format --check src/`
- **Build:** `uv build`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `uv run ruff check src/` exits 0. `uv run ruff format --check src/` exits 0. `uv run mypy src/corpus_council/core/` exits 0. `uv run pytest` exits 0 with all tests passing and coverage >= 80% on `core/`. `uv build` exits 0. All six FastAPI endpoints respond correctly. Both CLI modes (`chat`, `collect`) execute end-to-end against a real test corpus and council.
- **Max task tries:** 4
