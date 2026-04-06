# Corpus Council

A Python API and CLI for LLM-based conversations grounded in a curated knowledge corpus. Every response is routed through a **hierarchical council** — a set of markdown-defined AI personas with assigned authority levels that debate and validate answers before they are returned.

Two interaction modes:

- **Conversation** — ask questions, brainstorm, or seek advice. The council draws from the corpus to answer accurately in a consistent voice.
- **Collection** — structured interview mode that gathers specific information from the user, following a plan defined by the council.

The council is fully configuration-driven. Each persona is a markdown file with YAML front matter defining its personality, authority tier, and escalation rule. Higher-authority voices can override lower-authority ones. No behavioral logic lives in Python source.

## Setup

```bash
# Install dependencies
uv sync

# Set your LLM API key
export ANTHROPIC_API_KEY=your_key_here

# Add corpus documents (.md or .txt) to corpus/
# Add council persona files to council/
# Edit config.yaml to configure providers, models, and paths

# Ingest and embed the corpus
uv run corpus-council ingest corpus/
uv run corpus-council embed

# Start the API server
uv run corpus-council serve
```

> Alternatively, activate the virtualenv (`source .venv/bin/activate`) and use `corpus-council` directly.

## Usage

```bash
# Single-turn query
uv run corpus-council query user1234 "What is the refund policy?"

# Interactive conversation
uv run corpus-council chat user1234

# Single-turn query using the consolidated (2-call) deliberation mode
uv run corpus-council query user1234 "What is the refund policy?" --mode consolidated

# Interactive conversation in consolidated mode
uv run corpus-council chat user1234 --mode consolidated

# Structured data collection session
uv run corpus-council collect user1234 --plan signup

# Resume an existing collection session
uv run corpus-council collect user1234 --session <session_id>

# Ingest corpus documents
uv run corpus-council ingest /path/to/corpus/

# Generate embeddings
uv run corpus-council embed

# Start the API server (default: 127.0.0.1:8000)
uv run corpus-council serve --host 0.0.0.0 --port 8000
```

## Deliberation Modes

The council supports two deliberation modes, selectable per request or as a default in `config.yaml`.

| Mode | LLM calls | Description |
|------|-----------|-------------|
| `sequential` (default) | 2N+1 (N = council size) | Each member deliberates in turn; a final synthesizer resolves the result. Slower but each member sees prior context. |
| `consolidated` | 2 | All members respond in a single call, then an evaluator synthesizes the final answer. Faster — sub-30s for a 6-member council. |

**Set the default in `config.yaml`:**
```yaml
deliberation_mode: sequential  # or: consolidated
```

**Override per request via CLI:**
```bash
uv run corpus-council query user1234 "Your question" --mode consolidated
```

**Override per request via API:**
```json
{ "user_id": "user1234", "message": "Your question", "mode": "consolidated" }
```

Priority order: per-request flag/field → `config.yaml` → `sequential` default.

## Workflow

**1. Define your corpus** — place `.md` or `.txt` knowledge files in `corpus/`. These are the documents the council draws from when answering.

**2. Define your council** — add persona markdown files to `council/`. Each file has YAML front matter:

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

**3. Configure** — edit `config.yaml` to set LLM provider/model, embedding model, directory paths, and `deliberation_mode` (`sequential` or `consolidated`). API keys are always set via environment variables, never in config.

**4. Ingest and embed** — run `uv run corpus-council ingest` then `uv run corpus-council embed` to chunk documents and build the vector index in ChromaDB.

**5. Interact** — use `uv run corpus-council chat` for conversation mode or `uv run corpus-council collect` for structured interview mode. The full API is also available at `http://localhost:8000/docs` after `uv run corpus-council serve`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/conversation` | Single conversation turn |
| POST | `/collection/start` | Start a collection session |
| POST | `/collection/respond` | Respond to the current collection prompt |
| GET | `/collection/{user_id}/{session_id}` | Get session status |
| POST | `/corpus/ingest` | Ingest corpus documents |
| POST | `/corpus/embed` | Embed ingested chunks into ChromaDB |

`POST /conversation`, `POST /collection/start`, and `POST /collection/respond` each accept an optional `"mode": "sequential" | "consolidated"` field. Omitting it uses the `deliberation_mode` from `config.yaml`. An invalid value returns HTTP 422.
