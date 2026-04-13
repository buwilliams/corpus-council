# Corpus Council

A Python API and CLI for LLM-based conversations grounded in a curated knowledge corpus. Every response is routed through a **hierarchical council** — a set of markdown-defined AI personas with assigned authority levels that debate and validate answers before they are returned.

Interactions are driven by **goals** — named, file-defined configurations that specify a desired outcome, a council composition, and a corpus scope. New interaction types are added by authoring a markdown file and running `goals process`, with no Python source changes required.

## Setup

```bash
# Install dependencies
uv sync

# Set your LLM API key
export ANTHROPIC_API_KEY=your_key_here

# Create data_dir and conventional subdirectories
mkdir -p data/corpus data/council data/goals
# Add corpus documents (.md or .txt) to data/corpus/
# Add council persona files to data/council/
# Add goal files to data/goals/
# Edit config.yaml to set data_dir and other options

# Ingest and embed the corpus
uv run corpus-council ingest data/corpus/
uv run corpus-council embed

# Process goal files into the manifest
uv run corpus-council goals process

# Start the API server
uv run corpus-council serve
```

> Alternatively, activate the virtualenv (`source .venv/bin/activate`) and use `corpus-council` directly.

## Usage

```bash
# Start an interactive chat session with a named goal
uv run corpus-council chat <user-id> --goal intake

# Resume an existing conversation
uv run corpus-council chat <user-id> --goal intake --session <conversation-id>

# Override deliberation mode for the session
uv run corpus-council chat <user-id> --goal intake --mode consolidated

# Process goal files and write goals_manifest.json
uv run corpus-council goals process

# Ingest corpus documents
uv run corpus-council ingest /path/to/corpus/

# Generate embeddings
uv run corpus-council embed

# Start the API server (default: 0.0.0.0:8000)
uv run corpus-council serve --host 0.0.0.0 --port 8000
```

## Goals

A **goal** is a markdown file that declares a desired outcome, a council composition, and a corpus scope. Goals are processed offline into `goals_manifest.json` and referenced at runtime by name.

**Goal file format** (`goals/my-goal.md`):

```
---
desired_outcome: "Human-readable description of what this goal is trying to accomplish."
corpus_path: "corpus"
council:
  - persona_file: "coach.md"     # relative to data_dir/council/
    authority_tier: 1             # 1 = highest authority
  - persona_file: "analyst.md"
    authority_tier: 2
---
Optional body text with additional context for the council.
```

**Workflow:**

1. Author a goal file in `goals/`
2. Run `corpus-council goals process` to validate and register it
3. Use it at runtime: `corpus-council chat <user-id> --goal <name>`

Two goal files ship with the project:

| Goal | Purpose |
|---|---|
| `intake` | Structured customer intake interview to gather user data |
| `create-plan` | Synthesize intake data with the corpus to produce a COM-B 6-week plan |

> **Note:** Both goals reference `coach.md` and `analyst.md` persona files. These are deployment-specific and must be created in `council/` before running `goals process`. See [`docs/goal-authoring-guide.md`](docs/goal-authoring-guide.md) for the persona file format.

See [`docs/goal-authoring-guide.md`](docs/goal-authoring-guide.md) for the full authoring reference.

## How It Works

1. A user message is received by the `/chat` endpoint.
2. The raw user message is encoded into a vector using `sentence-transformers/all-MiniLM-L6-v2`.
3. ChromaDB is queried for the top-K corpus chunks closest to that vector by cosine similarity (default: 5).
4. The retrieved chunks are formatted with source attribution and injected into every LLM prompt — no LLM decides what to retrieve.
5. The active goal's council members deliberate using the user message and the retrieved chunks as shared context.
6. In **parallel** mode all non-position-1 members respond concurrently with no visibility into each other's responses; the position-1 member synthesizes all independent responses into the final answer.
7. In **consolidated** mode all members respond in a single LLM call, then a second call produces the synthesized final answer.
8. If any member triggers its escalation rule, all members still complete; escalation flags are collected post-flight and the position-1 member resolves the concern during synthesis.
9. The final synthesized response is returned to the caller and the turn is appended to the conversation history.

## Deliberation Modes

The council supports two deliberation modes, selectable per request or as a default in `config.yaml`.

| Mode | LLM calls | Description |
|------|-----------|-------------|
| `parallel` (default) | N+1 (N = non-position-1 members) | Each member deliberates independently with no visibility into other members' responses; the position-1 member synthesizes all responses. Concurrent — wall-clock time ~2 serial LLM round-trips. |
| `consolidated` | 2 | All members respond in a single call, then an evaluator synthesizes the final answer. Faster — sub-30s for a 6-member council. |

**Set the default in `config.yaml`:**
```yaml
deliberation_mode: parallel  # or: consolidated
```

**Override per request via CLI:**
```bash
uv run corpus-council chat <user-id> --goal intake --mode consolidated
```

**Override per request via API:**
```json
{ "goal": "intake", "user_id": "user0001", "message": "Your question", "mode": "consolidated" }
```

Priority order: per-request flag/field → `config.yaml` → `parallel` default.

## Workflow

**1. Define your corpus** — place `.md` or `.txt` knowledge files in `data_dir/corpus/`. These are the documents the council draws from when answering.

**2. Define your council** — add persona markdown files to `data_dir/council/`. Each file has YAML front matter:

```yaml
---
name: Domain Expert
persona: A seasoned expert who values precision above all else
primary_lens: factual accuracy
position: 1
role_type: synthesizer
escalation_rule: Halt if response contradicts established evidence
---
Additional context passed to this persona's prompts.
```

Lower `position` = higher authority. Position 1 always has final say.

**3. Define your goals** — add goal markdown files to `data_dir/goals/`. Each goal declares a `desired_outcome`, a `council` list (persona files + authority tiers), and a `corpus_path`. See [`docs/goal-authoring-guide.md`](docs/goal-authoring-guide.md).

**4. Configure** — edit `config.yaml` to set LLM provider/model, embedding model, `data_dir`, and `deliberation_mode`. API keys are always set via environment variables, never in config. Prompt templates are bundled with the package and are not user-configurable.

All content and generated artifacts live under a single `data_dir`. Set it in `config.yaml`:

```yaml
data_dir: data  # all subdirectories below are resolved relative to this path
```

The conventional subdirectory layout under `data_dir`:

| Subdirectory | Purpose |
|---|---|
| `corpus/` | Raw corpus documents (.md, .txt) |
| `council/` | Council persona markdown files |
| `goals/` | Goal markdown files |
| `chunks/` | Processed corpus chunk JSON files (written by `ingest`) |
| `embeddings/` | ChromaDB vector store (written by `embed`) |
| `users/` | User conversation data |
| `goals_manifest.json` | Goals manifest (written by `goals process`) |

> **Migration note:** If upgrading from a version that used `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path` in `config.yaml`: remove those keys. corpus-council will raise a clear error if they are present. Move your content directories under `data_dir/` using the conventional names above.

**5. Ingest, embed, and process** — run `ingest` then `embed` to chunk documents and build the vector index. Run `goals process` to register goal files into `goals_manifest.json`.

**6. Query** — use `corpus-council chat <user-id> --goal <name>` for interactive sessions. The full API is also available at `http://localhost:8000/docs` after `corpus-council serve`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Goal-aware chat turn — requires `goal`, `user_id`, `message`; optional `conversation_id`, `mode` |
| POST | `/corpus/ingest` | Ingest corpus documents |
| POST | `/corpus/embed` | Embed ingested chunks into ChromaDB |

**`POST /chat` request body:**
```json
{
  "goal": "intake",
  "user_id": "user0001",
  "message": "Your question here",
  "conversation_id": "optional-uuid-to-continue-a-prior-turn",
  "mode": "parallel"
}
```

- `goal` (required) — name of a registered goal from `goals_manifest.json`
- `user_id` (required) — caller-supplied identifier (minimum 4 characters)
- `message` (required) — the user's input
- `conversation_id` (optional) — omit to start a new conversation; supply to continue an existing one
- `mode` (optional) — `"parallel"` or `"consolidated"`; omit to use `config.yaml` default

**Responses:**
- `200` — `{ "response": "...", "goal": "intake", "conversation_id": "uuid" }`
- `400` — invalid `conversation_id` (e.g. path traversal attempt)
- `404` — goal name not found in manifest
- `422` — invalid `mode` value or missing required field
