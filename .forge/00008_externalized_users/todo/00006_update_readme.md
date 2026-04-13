# Task 00006: Update README.md

## Role
programmer

## Objective
Update `/home/buddy/projects/corpus-council/README.md` to reflect the simplified config: document the conventional subdirectory layout under `data_dir`, remove references to the five deprecated config keys (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`), and add a migration note for existing deployments.

## Context
File to modify: `/home/buddy/projects/corpus-council/README.md`

**Current README state** (relevant sections):
- The "Configure" section (Step 4 in the Workflow) currently documents `goals_dir`, `personas_dir`, and `goals_manifest_path` in a config table.
- The Setup section tells users to "Edit config.yaml to configure providers, models, and paths".

**Target README state** — changes needed:
1. **Remove the config table** in the Workflow section that documents `goals_dir`, `personas_dir`, and `goals_manifest_path` as explicit config keys.
2. **Add a conventional layout table** after the `data_dir` mention, showing the fixed subdirectory structure:

   | Subdirectory | Purpose |
   |---|---|
   | `corpus/` | Raw corpus documents (.md, .txt) |
   | `council/` | Council persona markdown files |
   | `goals/` | Goal markdown files |
   | `chunks/` | Processed corpus chunk JSON files (written by `ingest`) |
   | `embeddings/` | ChromaDB vector store (written by `embed`) |
   | `users/` | User conversation data |
   | `goals_manifest.json` | Goals manifest (written by `goals process`) |

3. **Update the "Configure" step** (Step 4 in Workflow) to say: "Edit `config.yaml` to set LLM provider/model, embedding model, `data_dir`, and `deliberation_mode`. All content directories (`corpus/`, `council/`, `goals/`) are resolved by convention under `data_dir`. API keys are always set via environment variables, never in config."

4. **Add a migration note** near the config section (can be a `> **Migration note:**` blockquote):
   "If you are upgrading from a version that used `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path` in `config.yaml`: remove those keys. corpus-council will raise a clear error if they are present. Move your content directories to the conventional locations under `data_dir/`."

5. **Update the Setup section** initial instructions to replace "Add corpus documents to corpus/" with "Place your corpus documents in `data_dir/corpus/`" etc., or simplify to "Set `data_dir` in `config.yaml` — corpus-council will read `data_dir/corpus/`, `data_dir/council/`, `data_dir/goals/` by convention."

The constitution's `README.md` requirement: "Any change to API endpoints, request/response shapes, CLI commands, deliberation modes, configuration keys, or architecture must be reflected in `README.md` before the spec is considered done." The config key change qualifies.

This task depends on Task 00001 and Task 00005.

## Steps
1. Read `/home/buddy/projects/corpus-council/README.md` in full.
2. Remove the config table that lists `goals_dir`, `personas_dir`, `goals_manifest_path` as configurable keys.
3. Update the "Configure" step description to describe the conventional subdir approach.
4. Add the conventional layout table (showing all subdirs under `data_dir`).
5. Add a migration note blockquote.
6. Update the Setup section initial checklist to match the new directory structure.
7. Confirm no remaining references to the five deprecated config keys remain in the README as config keys (they can appear in the migration note as keys to remove, but not as currently-supported keys).

## Verification
- Structural: `grep -n "goals_dir\|personas_dir\|goals_manifest_path" /home/buddy/projects/corpus-council/README.md` returns only the migration note (not documentation of them as supported config keys).
- Structural: `grep -n "data_dir/corpus\|data_dir/council\|data_dir/goals\|conventional" /home/buddy/projects/corpus-council/README.md` returns matches confirming the conventional layout is documented.
- Structural: `grep -n "Migration note\|migration" /home/buddy/projects/corpus-council/README.md` returns a match.
- Behavioral: `uv run pytest` exits 0 (README changes do not affect tests).
- Behavioral: `uv run ruff check src/` exits 0.
- Behavioral: `uv run mypy src/` exits 0.
- Global Constraint: No new packages in `pyproject.toml`.
- Dynamic: `uv run pytest` exits 0 — README changes are non-breaking.

## Done When
- [ ] `README.md` does not document `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path` as supported config keys.
- [ ] `README.md` documents the conventional subdirectory layout under `data_dir`.
- [ ] `README.md` contains a migration note for existing deployments.
- [ ] `uv run pytest` exits 0.

## Save Command
```
git add README.md && git commit -m "task-00006: update README — simplified config reference, conventional subdir layout, migration note"
```
