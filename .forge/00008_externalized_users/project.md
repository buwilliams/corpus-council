# Project Spec: Externalized Users

## Goal

Establish in the constitution that a single deployer-controlled `data_dir` is the one
source of truth for all deployment data — corpus content, council personas, goals,
processed chunks, embeddings, and user conversations. Eliminate the current proliferation
of separate path config keys (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`,
`goals_manifest_path`) in favor of conventional subdirectory names under `data_dir`.
After this change a deployer sets one path and corpus-council finds everything it needs
by convention: `data_dir/corpus/`, `data_dir/council/`, `data_dir/goals/`,
`data_dir/chunks/`, `data_dir/embeddings/`, `data_dir/users/`.

## Why This Matters

The current config has five path keys that all ultimately describe different facets of
"where the deployer's data lives." This is accidental complexity: FTA already keeps
corpus, council, and goals under a single `council-content/` directory — they just also
have to set three separate config paths pointing into it. A new deployer faces the same
unnecessary ceremony. Worse, users and internal processing data (chunks, embeddings)
live under a different root (`data_dir`) from the corpus content, splitting ownership
across two directories with no principled reason.

Collapsing to one `data_dir` with conventional subdirs enforces the ownership model
constitutionally: the deployer chooses one directory, owns everything in it, and
corpus-council reads and writes to conventional locations within it. No ambiguity
about what the deployer controls.

## Deliverables

- [ ] `constitution.md` updated:
    - New Core Principle: one deployer-controlled `data_dir`; all platform data lives
      under conventional subdirectory names within it; the deployer owns the entire tree
    - Hard Constraint added: no configurable path keys beyond `data_dir`; subdirectory
      layout is fixed by convention, not configuration
    - "Out of Scope — Forever" updated: owning or relocating deployer data; per-subdir
      path overrides
- [ ] `AppConfig` simplified: remove `corpus_dir`, `council_dir`, `goals_dir`,
  `personas_dir`, `goals_manifest_path`; add derived `@property` accessors or
  equivalent for each conventional path (`corpus_dir`, `council_dir`, etc.) based on
  `data_dir`
- [ ] `load_config()` updated: stop reading the removed keys; warn or error if any
  are present (explicit migration signal)
- [ ] All callsites updated to use the derived paths
- [ ] `config.yaml` and `config.yaml.example` updated: remove the five path keys;
  document the conventional subdirectory layout in comments
- [ ] FTA's `corpus-council.config.yaml` updated: remove `corpus_dir`, `council_dir`,
  `goals_dir`, `personas_dir`, `goals_manifest_path`; set `data_dir` to the single root
  that encompasses all their content (e.g. the directory containing `corpus/`,
  `council/`, `goals/`, `users/`)
- [ ] FTA's directory layout verified/updated to match conventions if needed
- [ ] `README.md` updated: simplified config reference; conventional subdirectory layout
  documented; migration note for existing deployments
- [ ] All existing tests pass; new/updated tests cover the simplified config parsing and
  derived path accessors

## Tech Stack

- Language: Python
- Runtime / Platform: FastAPI + uvicorn
- Key dependencies: existing (no new deps)
- Build tool: uv
- Package manager: uv

## Architecture Overview

`AppConfig` retains only `data_dir` as a configurable path. All other paths are derived
by convention:

| Subdirectory        | Purpose                            |
|---------------------|------------------------------------|
| `corpus/`           | Raw corpus documents               |
| `council/`          | Council persona markdown files     |
| `goals/`            | Goals markdown files               |
| `chunks/`           | Processed corpus chunk JSON files  |
| `embeddings/`       | ChromaDB vector store              |
| `users/`            | User conversation data (FileStore) |

`goals_manifest.json` lives at `data_dir/goals_manifest.json`.

`AppConfig` exposes these as computed properties (or equivalent) so callsites read
`config.corpus_dir` as before — the change is transparent beyond config loading and
`AppConfig` itself. `chroma_collection` and `deliberation_mode` remain configurable
as they are behavioral, not path, settings.

## Testing Requirements

- Unit tests: `test_config.py` — simplified YAML parses correctly; removed keys trigger
  a clear error or warning; all derived paths resolve relative to `data_dir`
- Unit tests: `test_store.py` — `FileStore` initialized with `config.users_dir`
  (derived) writes to `data_dir/users/`
- Integration tests: existing chat, conversation, and corpus endpoint tests pass
  unmodified
- Test framework: pytest
- Coverage threshold: existing bar maintained
- What must never be mocked: filesystem operations in store tests — use tmp_path

## Code Quality

- Linter / static analysis: ruff
- Formatter: ruff format
- Type checking: mypy
- Commands that must exit 0: `uv run ruff check src/`, `uv run mypy src/`, `uv run pytest`

## Constraints

- The five removed config keys must not silently be ignored if present — warn loudly
  so existing deployers know to migrate
- `chroma_collection` and `deliberation_mode` remain as explicit config keys
- No new Python dependencies
- Constitution changes must be the first task

## Performance Requirements

None — path-resolution change only.

## Security Considerations

`data_dir` is operator-supplied via config file (trusted). Path traversal protection
in `FileStore.user_dir()` is unchanged.

## Out of Scope

- Per-subdirectory path overrides (the whole point is to remove them)
- Non-filesystem storage backends
- Automatic data migration when directory layout changes
- Auth or session management

---

## Global Constraints
<!-- Generated by Forge spec agent — edit to adjust rules applied to every task -->

- No hardcoded behavioral rules in source code — all rules live in council persona markdown files
- No relational database, message queue, or external service dependency unless a flat file is technically insufficient
- All LLM calls must use markdown prompt templates — no inline prompt strings in Python source
- Python throughout — no polyglot backend
- `uv run ruff check src/` must exit 0 with no errors or warnings
- `uv run mypy src/` must exit 0 with no errors (mypy strict mode is enabled in `pyproject.toml`)
- `uv run pytest` must exit 0 with all tests passing
- No new Python dependencies — `pyproject.toml` dependency list must not grow
- The five removed config keys (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`) must raise a clear error or warning when present in a config file — silent acceptance is forbidden
- No test stubs, mocks, or smoke-tests for filesystem operations in store tests — use `tmp_path` and real file I/O
- `constitution.md` changes must be completed before any code changes — constitution is the first deliverable

## Dynamic Verification
- **Exercise command:** `uv run pytest`

## Execution
- **Test:** `uv run pytest`
- **Typecheck:** `uv run mypy src/`
- **Lint:** `uv run ruff check src/`
- **Completion condition:** All tasks in `done/`. Zero tasks in `todo/`, `working/`, or `blocked/`. `uv run ruff check src/` exits 0. `uv run mypy src/` exits 0. `uv run pytest` exits 0 with all tests passing.
- **Max task tries:** 3
