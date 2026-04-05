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
# Interactive conversation with a user
uv run corpus-council chat user1234

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

**3. Configure** — edit `config.yaml` to set LLM provider/model, embedding model, and directory paths. API keys are always set via environment variables, never in config.

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
