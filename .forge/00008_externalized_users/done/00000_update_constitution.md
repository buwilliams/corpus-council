# Task 00000: Update Constitution

## Role
programmer

## Objective
Update `/home/buddy/projects/corpus-council/.forge/constitution.md` to establish the one-`data_dir` ownership model as a Core Principle and Hard Constraint, and extend "Out of Scope — Forever" to prohibit per-subdirectory path overrides. This must be the first deliverable, completed before any code changes.

## Context
The constitution lives at `/home/buddy/projects/corpus-council/.forge/constitution.md`. It currently has five sections: Core Principles, Quality Bar, Hard Constraints, Out of Scope — Forever, and Review Standards.

The project spec requires three specific constitution changes:
1. **New Core Principle**: one deployer-controlled `data_dir`; all platform data lives under conventional subdirectory names within it; the deployer owns the entire tree.
2. **New Hard Constraint**: no configurable path keys beyond `data_dir`; subdirectory layout is fixed by convention, not configuration.
3. **"Out of Scope — Forever" addition**: owning or relocating deployer data; per-subdir path overrides.

The conventional subdirectory layout is:
- `corpus/` — raw corpus documents
- `council/` — council persona markdown files
- `goals/` — goals markdown files
- `chunks/` — processed corpus chunk JSON files
- `embeddings/` — ChromaDB vector store
- `users/` — user conversation data
- `goals_manifest.json` — goals manifest (at `data_dir` root, not in a subdir)

Tech stack: No code changes in this task — documentation only.

## Steps
1. Read `/home/buddy/projects/corpus-council/.forge/constitution.md` in full.
2. Add a new Core Principle (number it as the next sequential principle after the existing ones):
   "**One deployer-controlled data directory.** A single `data_dir` is the sole root for all deployment data — corpus content, council personas, goals, processed chunks, embeddings, and user conversations. All platform data lives under conventional subdirectory names within `data_dir`; the deployer owns the entire tree. No code path reads or writes deployment data outside `data_dir`."
3. Add a new Hard Constraint to the Hard Constraints section:
   "No configurable path keys beyond `data_dir`. The subdirectory layout under `data_dir` is fixed by convention: `corpus/`, `council/`, `goals/`, `chunks/`, `embeddings/`, `users/`, and `goals_manifest.json` at the root. Per-subdirectory path overrides are prohibited."
4. Extend "Out of Scope — Forever" with two new bullet points:
   - "Owning, relocating, or migrating deployer data outside the `data_dir` tree."
   - "Per-subdirectory path overrides — the conventional layout is fixed; deployers set `data_dir` and corpus-council finds everything by convention."
5. Confirm the constitution reads coherently end-to-end.

## Verification
- Structural: `/home/buddy/projects/corpus-council/.forge/constitution.md` contains the phrase `data_dir` in the Core Principles section.
- Structural: the Hard Constraints section contains the phrase "No configurable path keys beyond `data_dir`".
- Structural: the "Out of Scope — Forever" section contains "Per-subdirectory path overrides".
- Dynamic: `uv run pytest` exits 0 (no code changed, so tests should remain green).
- Lint: `uv run ruff check src/` exits 0 (no code changed).
- Typecheck: `uv run mypy src/` exits 0 (no code changed).

## Done When
- [ ] `constitution.md` contains a Core Principle establishing `data_dir` as the single deployer-controlled root.
- [ ] `constitution.md` Hard Constraints prohibit any configurable path keys beyond `data_dir`.
- [ ] `constitution.md` "Out of Scope — Forever" includes per-subdirectory path overrides.
- [ ] All verification checks pass.

## Save Command
```
git add .forge/constitution.md && git commit -m "task-00000: update constitution — one data_dir, conventional subdir layout"
```
