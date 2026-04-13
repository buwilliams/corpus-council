# Task 00005: Update config.yaml

## Role
programmer

## Objective
Update `/home/buddy/projects/corpus-council/config.yaml` to remove the five deprecated path keys (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`) and add a comment block documenting the conventional subdirectory layout under `data_dir`. If `config.yaml.example` exists, update it the same way.

## Context
File to modify: `/home/buddy/projects/corpus-council/config.yaml`

**Current state** of `config.yaml`:
```yaml
# API keys are not stored here — use environment variables (ANTHROPIC_API_KEY, etc.)

llm:
  provider: anthropic
  model: claude-sonnet-4-6

embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2

data_dir: data
corpus_dir: corpus
council_dir: council
goals_dir: goals
personas_dir: council
goals_manifest_path: goals_manifest.json

chunking:
  max_size: 512

retrieval:
  top_k: 5

chroma_collection: corpus
# Deliberation mode: "parallel" (default, 2N+1 LLM calls) or "consolidated" (2 LLM calls)
deliberation_mode: parallel
```

**Target state** — remove the five deprecated path keys; keep `data_dir`; add a comment block after `data_dir` that documents the conventional subdirectory layout:

```yaml
# API keys are not stored here — use environment variables (ANTHROPIC_API_KEY, etc.)

llm:
  provider: anthropic
  model: claude-sonnet-4-6

embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2

# All platform data lives under data_dir in conventional subdirectories:
#   corpus/       — raw corpus documents (.md, .txt)
#   council/      — council persona markdown files
#   goals/        — goal markdown files
#   chunks/       — processed corpus chunk JSON files (written by 'ingest')
#   embeddings/   — ChromaDB vector store (written by 'embed')
#   users/        — user conversation data
#   goals_manifest.json — goals manifest (written by 'goals process')
data_dir: data

chunking:
  max_size: 512

retrieval:
  top_k: 5

chroma_collection: corpus
# Deliberation mode: "parallel" (default, 2N+1 LLM calls) or "consolidated" (2 LLM calls)
deliberation_mode: parallel
```

**Note**: After this task, `uv run pytest tests/unit/test_config.py::test_load_config_returns_all_required_fields` should still pass because it loads the real `config.yaml` and checks `isinstance(config.corpus_dir, Path)` — which now works via the `@property` accessor.

**Check for config.yaml.example**: Run `ls /home/buddy/projects/corpus-council/` to confirm whether `config.yaml.example` exists. If it does, apply the same changes.

This task depends on Task 00001 (the removed keys now cause ValueError if present — so they must be gone from config.yaml before `load_config` is called at startup).

## Steps
1. Read `/home/buddy/projects/corpus-council/config.yaml` in full.
2. Remove the five lines: `corpus_dir: corpus`, `council_dir: council`, `goals_dir: goals`, `personas_dir: council`, `goals_manifest_path: goals_manifest.json`.
3. Add the comment block documenting conventional subdirectories (as shown in Context above) immediately before the `data_dir: data` line.
4. Check if `config.yaml.example` exists at the project root. If so, read it and apply the same changes.
5. Run `uv run pytest` to confirm all tests still pass (the real config.yaml is now clean of deprecated keys).

## Verification
- Structural: `grep -n "corpus_dir\|council_dir\|goals_dir\|personas_dir\|goals_manifest_path" /home/buddy/projects/corpus-council/config.yaml` returns no matches.
- Structural: `grep -n "data_dir" /home/buddy/projects/corpus-council/config.yaml` returns the `data_dir: data` line and the comment block.
- Structural: `grep -n "corpus/\|council/\|goals/\|chunks/\|embeddings/\|users/" /home/buddy/projects/corpus-council/config.yaml` returns matches in comments (the layout documentation).
- Behavioral: `uv run pytest` exits 0.
- Behavioral: `uv run ruff check src/` exits 0.
- Behavioral: `uv run mypy src/` exits 0.
- Global Constraint: No new packages in `pyproject.toml`.
- Dynamic: `python -c "from corpus_council.core.config import load_config; from pathlib import Path; c = load_config(Path('config.yaml')); print(c.corpus_dir, c.council_dir, c.goals_manifest_path)"` prints paths containing `/corpus`, `/council`, `/goals_manifest.json` respectively (no error).

## Done When
- [ ] `config.yaml` does not contain `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path` keys.
- [ ] `config.yaml` contains a comment block documenting the conventional subdirectory layout.
- [ ] `uv run pytest` exits 0.

## Save Command
```
git add config.yaml && git commit -m "task-00005: update config.yaml — remove deprecated path keys, document conventional layout"
```
