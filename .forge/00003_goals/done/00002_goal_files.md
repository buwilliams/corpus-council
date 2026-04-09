# Task 00002: Author goals/intake.md and goals/create-plan.md

## Role
product-manager

## Objective
Create the `goals/` directory at the project root and write two valid goal markdown files: `goals/intake.md` (for conducting a structured customer intake interview) and `goals/create-plan.md` (for synthesizing gathered customer data with the corpus to produce a COM-B 6-week plan). Both files must be parseable by `parse_goal_file` from Task 00001, reference real persona files that exist in `council/`, and declare valid `desired_outcome`, `council`, and `corpus_path` fields. The `council/` directory is populated by the deployment; for the goals to be usable, the persona files referenced must actually exist. Since the real `council/` is populated by the deployer, use a convention: reference filenames by their expected basename (e.g., `advisor.md`) and document this requirement clearly.

## Context
Task 00000 added `goals_dir: Path` and `personas_dir: Path` to `AppConfig`, defaulting to `goals` and `council` respectively. Task 00001 implemented `parse_goal_file(path, personas_dir)` which reads YAML front matter from a markdown goal file and validates persona file existence inside `personas_dir`.

**Goal file format** (from Task 00001):
```markdown
---
desired_outcome: "Desired outcome text here"
corpus_path: "corpus"
council:
  - persona_file: "filename.md"
    authority_tier: 1
  - persona_file: "other.md"
    authority_tier: 2
---
Optional body text with additional context or instructions for the council.
```

**Fields required** by `parse_goal_file`:
- `desired_outcome` (string, required): what this interaction is meant to accomplish
- `corpus_path` (string, required): relative path or scope name for corpus access (e.g., `"corpus"`)
- `council` (list, required): ordered list of council members, each with `persona_file` (filename relative to `personas_dir`) and `authority_tier` (integer, lower = higher authority)

**Persona file convention**: The `council/` directory is deployment-specific and gitignored (see `.gitignore`: `council/*`). For the goal files to be syntactically valid and parseable in tests, they must reference persona files that will exist. The integration tests (Task 00006) will create fake persona files in `tmp_path/council/` that match whatever names these goal files reference. Therefore, use simple, predictable names like `coach.md` and `analyst.md` — names the test fixtures can create.

**Constraint from project.md**: `intake.md` and `create-plan.md` are deployment-specific examples — their content is configuration, not platform logic. The COM-B plan logic lives entirely in the `create-plan` goal file and council configuration, not in Python source.

**`corpus_path`** can be the literal string `"corpus"` — the runtime resolves this as the configured corpus directory.

## Steps
1. Create the directory `/home/buddy/projects/corpus-council/goals/` (it does not yet exist).
2. Write `/home/buddy/projects/corpus-council/goals/intake.md` with:
   - `desired_outcome`: a clear description of conducting a structured customer intake interview to gather user data (e.g., name, goals, current situation, motivation)
   - `corpus_path: "corpus"`
   - `council`: at least two council members — e.g., `coach.md` (authority_tier 1) and `analyst.md` (authority_tier 2)
   - Body: a brief paragraph describing the council's collective intent for the intake session
3. Write `/home/buddy/projects/corpus-council/goals/create-plan.md` with:
   - `desired_outcome`: a clear description of synthesizing gathered customer data with the corpus to produce a COM-B (Capability, Opportunity, Motivation–Behaviour) 6-week plan
   - `corpus_path: "corpus"`
   - `council`: at least two council members referencing the same persona filenames as `intake.md`
   - Body: a brief paragraph describing the COM-B framework focus and plan structure
4. Add a `goals/.gitkeep` file so the directory is tracked (analogous to `corpus/.gitkeep` and `council/.gitkeep` in the existing `.gitignore` setup).
5. Verify that both files parse correctly using the `parse_goal_file` function — since persona files won't exist in the real `council/` directory (it's gitignored and empty), this is best verified in the unit/integration tests (Task 00005). For now, validate the YAML front matter is correct by running:
   ```bash
   uv run python -c "
   import frontmatter
   for f in ['goals/intake.md', 'goals/create-plan.md']:
       post = frontmatter.load(f)
       assert 'desired_outcome' in post.metadata, f'{f} missing desired_outcome'
       assert 'corpus_path' in post.metadata, f'{f} missing corpus_path'
       assert 'council' in post.metadata, f'{f} missing council'
       assert isinstance(post.metadata['council'], list), f'{f} council must be a list'
       for entry in post.metadata['council']:
           assert 'persona_file' in entry, f'{f} council entry missing persona_file'
           assert 'authority_tier' in entry, f'{f} council entry missing authority_tier'
       print(f'{f}: OK')
   "
   ```
6. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/` to confirm no regressions.

## Verification
- Structural: `goals/intake.md` exists and contains YAML front matter with `desired_outcome`, `corpus_path`, and `council` fields
- Structural: `goals/create-plan.md` exists and contains YAML front matter with `desired_outcome`, `corpus_path`, and `council` fields
- Structural: Each `council` entry in both files has `persona_file` (string) and `authority_tier` (integer) fields
- Structural: Both goal files reference the same persona filenames (so test fixtures need only create one set)
- Behavioral: The Python snippet in Step 5 above exits 0 — both files parse as valid YAML front matter with all required keys
- Behavioral: `uv run mypy src/` exits 0
- Behavioral: `uv run ruff check .` exits 0
- Constraint (goal files are markdown — no YAML-only or JSON-only definitions): Both files are `.md` with a body section beyond just the YAML front matter
- Constraint (no hardcoded behavioral rules in Python source): These are configuration files, not Python source — constraint is satisfied by design
- Dynamic: `uv run python -c "import frontmatter; p = frontmatter.load('goals/intake.md'); print(p.metadata['desired_outcome'])"` prints non-empty string without error

## Done When
- [ ] `goals/intake.md` exists with valid front matter and a meaningful `desired_outcome`
- [ ] `goals/create-plan.md` exists with valid front matter and a meaningful `desired_outcome`
- [ ] Both files reference persona filenames that integration tests can create (e.g., `coach.md`, `analyst.md`)
- [ ] YAML parsing smoke test passes
- [ ] All verification checks pass

## Save Command
```
git add goals/ && git commit -m "task-00002: add goals/intake.md and goals/create-plan.md goal files"
```
