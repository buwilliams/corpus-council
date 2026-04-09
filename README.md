# Corpus Council

A Python API and CLI for LLM-based conversations grounded in a curated knowledge corpus. Every response is routed through a **hierarchical council** — a set of markdown-defined AI personas with assigned authority levels that debate and validate answers before they are returned.

Interactions are driven by **goals** — named, file-defined configurations that specify a desired outcome, a council composition, and a corpus scope. New interaction types are added by authoring a markdown file and running `goals process`, with no Python source changes required.

## Setup

```bash
# Install dependencies
uv sync

# Set your LLM API key
export ANTHROPIC_API_KEY=your_key_here

# Add corpus documents (.md or .txt) to corpus/
# Add council persona files to council/
# Add goal files to goals/
# Edit config.yaml to configure providers, models, and paths

# Ingest and embed the corpus
uv run corpus-council ingest corpus/
uv run corpus-council embed

# Process goal files into the manifest
uv run corpus-council goals process

# Start the API server
uv run corpus-council serve
```

> Alternatively, activate the virtualenv (`source .venv/bin/activate`) and use `corpus-council` directly.

## Usage

```bash
# Single-turn query using a named goal
uv run corpus-council query --goal intake "Tell me about yourself."

# Single-turn query with explicit deliberation mode
uv run corpus-council query --goal intake "Tell me about yourself." --mode consolidated

# Process goal files and write goals_manifest.json
uv run corpus-council goals process

# Ingest corpus documents
uv run corpus-council ingest /path/to/corpus/

# Generate embeddings
uv run corpus-council embed

# Start the API server (default: 127.0.0.1:8000)
uv run corpus-council serve --host 0.0.0.0 --port 8000
```

## Goals

A **goal** is a markdown file that declares a desired outcome, a council composition, and a corpus scope. Goals are processed offline into `goals_manifest.json` and referenced at runtime by name.

**Goal file format** (`goals/my-goal.md`):

```yaml
---
desired_outcome: "Human-readable description of what this goal is trying to accomplish."
corpus_path: "corpus"
council:
  - persona_file: "coach.md"     # relative to personas_dir
    authority_tier: 1             # 1 = highest authority
  - persona_file: "analyst.md"
    authority_tier: 2
---
Optional body text with additional context for the council.
```

**Workflow:**

1. Author a goal file in `goals/`
2. Run `corpus-council goals process` to validate and register it
3. Use it at runtime: `corpus-council query --goal <name> "<message>"`

Two goals ship with the project:

| Goal | Purpose |
|---|---|
| `intake` | Structured customer intake interview to gather user data |
| `create-plan` | Synthesize intake data with the corpus to produce a COM-B 6-week plan |

See [`docs/goal-authoring-guide.md`](docs/goal-authoring-guide.md) for the full authoring reference.

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
uv run corpus-council query --goal intake "Your question" --mode consolidated
```

**Override per request via API:**
```json
{ "message": "Your question", "goal": "intake", "mode": "consolidated" }
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

**3. Define your goals** — add goal markdown files to `goals/`. Each goal declares a `desired_outcome`, a `council` list (persona files + authority tiers), and a `corpus_path`. See [`docs/goal-authoring-guide.md`](docs/goal-authoring-guide.md).

**4. Configure** — edit `config.yaml` to set LLM provider/model, embedding model, directory paths, and `deliberation_mode`. API keys are always set via environment variables, never in config.

**5. Ingest, embed, and process** — run `ingest` then `embed` to chunk documents and build the vector index. Run `goals process` to register goal files into `goals_manifest.json`.

**6. Query** — use `corpus-council query --goal <name> "<message>"` for single-turn queries. The full API is also available at `http://localhost:8000/docs` after `corpus-council serve`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Single query turn — requires `goal`, `message`; optional `mode` |
| POST | `/corpus/ingest` | Ingest corpus documents |
| POST | `/corpus/embed` | Embed ingested chunks into ChromaDB |

**`POST /query` request body:**
```json
{
  "message": "Your question here",
  "goal": "intake",
  "mode": "sequential"
}
```

- `goal` (required) — name of a registered goal from `goals_manifest.json`
- `message` (required) — the user's input
- `mode` (optional) — `"sequential"` or `"consolidated"`; omit to use `config.yaml` default

**Responses:**
- `200` — `{ "response": "...", "goal": "intake" }`
- `404` — goal name not found in manifest
- `422` — invalid `mode` value or missing required field
