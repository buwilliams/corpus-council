# Task 00007: Add goal authoring guide documentation

## Role
product-manager

## Objective
Add a goal authoring guide to the project. The guide must be embedded as a module-level docstring in `src/corpus_council/core/goals.py` (so it is always co-located with the implementation and visible via `help(goals)`) AND written as a standalone document at `docs/goal-authoring-guide.md`. The guide must explain the goal file format (YAML front matter schema), the `goals process` command, and how to use `--goal <name>` at runtime. It must not contain any hardcoded behavioral rules or council selection logic — it is a format reference, not policy.

## Context
**Project.md deliverable**: "Documentation update: goal authoring guide explaining the file format and process step."

**Task 00001** defined the goal file format in code comments. **Task 00002** created `goals/intake.md` and `goals/create-plan.md` as real examples.

**Goal file schema** (to be documented):
```markdown
---
desired_outcome: "A human-readable description of what this goal is trying to accomplish."
corpus_path: "corpus"   # relative path or scope name for corpus retrieval
council:
  - persona_file: "filename.md"   # relative to personas_dir (config.personas_dir)
    authority_tier: 1              # integer; 1 = highest authority (synthesizer)
  - persona_file: "other.md"
    authority_tier: 2
---
Optional body text. This is passed to council members as additional context for the goal.
Any markdown content here is read as the goal's description body.
```

**Required guide sections**:
1. **Overview** — what a goal is, why goals exist, how they replace hardcoded interaction modes
2. **File Format** — the YAML front matter schema with field-by-field description; include a worked example
3. **Authority Tiers** — how `authority_tier` maps to deliberation order (tier 1 = position 1 = final synthesizer; higher tier = earlier in the chain, reviewed by lower tiers)
4. **Corpus Path** — what `corpus_path` means and how it is resolved
5. **Processing Goals** — how to run `corpus-council goals process`, what it produces (`goals_manifest.json`), idempotency guarantee
6. **Using a Goal at Runtime** — `corpus-council query --goal <name> <message>` and `POST /query` with `"goal": "<name>"`
7. **Path Safety** — note that `persona_file` paths are validated to stay within the personas directory; traversal attempts are rejected at process time
8. **Example** — show a complete working goal file (can reference `goals/intake.md`)

**Constraint from project.md**: Goal files are markdown — the guide must make clear that `.md` is the required format. The guide must NOT include any Python source code logic or suggest that behavioral rules belong in Python files.

**The `docs/goal-authoring-guide.md` file**: Create `docs/` if it does not exist. This is a documentation file explicitly requested by the user, so creating it is permitted.

**Module docstring in `goals.py`**: Add a concise docstring at the top of `goals.py` (below the `from __future__ import annotations` and before the imports) that summarizes the goal file format. This is for `help()` discoverability.

## Steps
1. Open `src/corpus_council/core/goals.py` (from Task 00001) and add a module-level docstring immediately after `from __future__ import annotations`:
   ```python
   """Goals model for corpus-council.

   A goal is a markdown file that declares a desired outcome, a list of council
   members (with authority tiers), and a corpus scope. Goals are pre-processed
   offline via ``corpus-council goals process`` into ``goals_manifest.json``.
   At runtime, ``--goal <name>`` loads the named goal from the manifest.

   Goal file format (YAML front matter in a ``.md`` file)::

       ---
       desired_outcome: "Human-readable description of the desired outcome."
       corpus_path: "corpus"
       council:
         - persona_file: "coach.md"   # relative to personas_dir
           authority_tier: 1          # 1 = highest authority
         - persona_file: "analyst.md"
           authority_tier: 2
       ---
       Optional body text with additional context for the council.

   See docs/goal-authoring-guide.md for the full authoring guide.
   """
   ```
2. Create `docs/` directory if it does not exist.
3. Write `docs/goal-authoring-guide.md` covering all eight sections listed in Context above. Use the worked examples from `goals/intake.md` and `goals/create-plan.md`. Keep the guide under 400 lines — focused and precise, not exhaustive.
4. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/` — the docstring addition must not break any of these. Run `uv run pytest` to confirm no regressions.

## Verification
- Structural: `docs/goal-authoring-guide.md` exists
- Structural: `docs/goal-authoring-guide.md` contains sections for: file format, authority tiers, corpus path, `goals process` command, runtime usage (`--goal` flag and `POST /query`), path safety, and a worked example
- Structural: `src/corpus_council/core/goals.py` has a module-level docstring that includes the goal file schema
- Structural: `docs/goal-authoring-guide.md` does NOT contain Python source code snippets that embed behavioral rules or council selection logic
- Behavioral: `uv run python -c "import corpus_council.core.goals; help(corpus_council.core.goals)"` prints the module docstring (non-empty output)
- Behavioral: `uv run mypy src/` exits 0
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run pytest` exits 0
- Constraint (goal files are markdown): The guide explicitly states `.md` is required and shows only markdown examples
- Dynamic: `uv run python -c "import corpus_council.core.goals; print(corpus_council.core.goals.__doc__[:80])"` prints the first 80 characters of the module docstring without error

## Done When
- [ ] `docs/goal-authoring-guide.md` exists with all required sections
- [ ] `goals.py` has a module-level docstring with the goal file format schema
- [ ] `uv run pytest` exits 0
- [ ] All verification checks pass

## Save Command
```
git add docs/goal-authoring-guide.md src/corpus_council/core/goals.py && git commit -m "task-00007: add goal authoring guide to docs/ and goals.py module docstring"
```
