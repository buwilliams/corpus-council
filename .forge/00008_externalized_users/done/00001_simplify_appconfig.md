# Task 00001: Simplify AppConfig and load_config

## Role
programmer

## Objective
Refactor `src/corpus_council/core/config.py` to remove `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, and `goals_manifest_path` as dataclass fields, and replace them with `@property` accessors derived from `self.data_dir`. Add `@property` accessors for `chunks_dir`, `embeddings_dir`, and `users_dir`. Update `load_config()` to raise `ValueError` with a clear migration message if any of the five removed keys are present in the YAML. Remove the `_resolve_path` calls for those five keys in `load_config()`.

## Context
File to modify: `/home/buddy/projects/corpus-council/src/corpus_council/core/config.py`

**Current state** — `AppConfig` is a `@dataclass` with these fields (among others):
- `data_dir: Path`
- `corpus_dir: Path`
- `council_dir: Path`
- `goals_dir: Path` (default: `Path("goals")`)
- `personas_dir: Path` (default: `Path("council")`)
- `goals_manifest_path: Path` (default: `Path("goals_manifest.json")`)

`load_config()` currently reads all five from YAML and passes them to the `AppConfig` constructor.

**Target state** — `AppConfig` retains only `data_dir: Path` as a configurable path field. The five removed fields become `@property` methods:
- `corpus_dir` → `self.data_dir / "corpus"`
- `council_dir` → `self.data_dir / "council"`
- `goals_dir` → `self.data_dir / "goals"`
- `personas_dir` → `self.data_dir / "council"` (same as `council_dir`)
- `goals_manifest_path` → `self.data_dir / "goals_manifest.json"`
- `chunks_dir` → `self.data_dir / "chunks"` (new, no prior field)
- `embeddings_dir` → `self.data_dir / "embeddings"` (new, no prior field)
- `users_dir` → `self.data_dir / "users"` (new, no prior field)

**Dataclass + @property compatibility**: In Python, a `@dataclass` can have `@property` methods as long as the property name does not collide with any dataclass field name. Since we are removing `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, and `goals_manifest_path` as fields, adding them back as `@property` methods is valid. All eight properties must have return type `-> Path`.

**Migration error** — `load_config()` must check the raw YAML dict for any of the five removed keys and raise `ValueError` with a message like:
```
"Config key 'corpus_dir' is no longer supported. Remove it from your config file; "
"the path is now derived as data_dir/corpus/ by convention."
```
Do this for each key: `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`. Check the raw dict **before** constructing `AppConfig`.

**Callsite impact**: All existing code that reads `config.corpus_dir`, `config.council_dir`, etc. continues to work unchanged because the properties return the same `Path` type. The only breaking callsite is `conftest.py` which _constructs_ `AppConfig(corpus_dir=..., ...)` with the old fields — that is handled in Task 00003.

There are also two `dataclasses.replace(config, corpus_dir=...)` calls:
- `src/corpus_council/cli/main.py` line 137: `modified_config = dataclasses.replace(config, corpus_dir=Path(path))`
- `src/corpus_council/api/routers/corpus.py` line 27: `modified_config = dataclasses.replace(config, corpus_dir=validated_path)`

`dataclasses.replace()` cannot replace properties — only fields. These callsites must be fixed in this task by replacing `dataclasses.replace(config, corpus_dir=x)` with a different pattern. The cleanest approach: pass the path directly to `ingest_corpus()` by making it accept an optional `corpus_dir` parameter, OR create a small helper. 

The simplest fix: in `ingest_corpus()` (in `corpus.py`), add an optional `corpus_dir: Path | None = None` parameter. When provided, use it instead of `config.corpus_dir`. Then update both callsites to call `ingest_corpus(config, corpus_dir=Path(path))` instead of using `dataclasses.replace`.

**Tech stack**: Python 3.12, mypy strict mode (`uv run mypy src/` must exit 0).

**Helper functions to retain**: `_resolve_path`, `_require_str`, `_require_int`, `_require_dict` — these remain unchanged except that `_resolve_path` is no longer called for the five removed keys.

## Steps
1. Read `/home/buddy/projects/corpus-council/src/corpus_council/core/config.py` in full.
2. Remove the five fields from the `AppConfig` dataclass: `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`.
3. Add eight `@property` methods to `AppConfig` (after the dataclass field declarations):
   - `corpus_dir(self) -> Path`: returns `self.data_dir / "corpus"`
   - `council_dir(self) -> Path`: returns `self.data_dir / "council"`
   - `goals_dir(self) -> Path`: returns `self.data_dir / "goals"`
   - `personas_dir(self) -> Path`: returns `self.data_dir / "council"`
   - `goals_manifest_path(self) -> Path`: returns `self.data_dir / "goals_manifest.json"`
   - `chunks_dir(self) -> Path`: returns `self.data_dir / "chunks"`
   - `embeddings_dir(self) -> Path`: returns `self.data_dir / "embeddings"`
   - `users_dir(self) -> Path`: returns `self.data_dir / "users"`
4. Update `load_config()`:
   a. After parsing the raw YAML into `data`, add a migration check that iterates over `("corpus_dir", "council_dir", "goals_dir", "personas_dir", "goals_manifest_path")` and raises `ValueError` if any key is present.
   b. Remove the three lines that resolve `goals_dir`, `personas_dir`, and `goals_manifest_path` via `_resolve_path`.
   c. Remove the `corpus_dir=...` and `council_dir=...` keyword args from the `AppConfig(...)` constructor call.
   d. Remove `goals_dir=goals_dir`, `personas_dir=personas_dir`, `goals_manifest_path=goals_manifest_path` from the constructor call.
5. Read `/home/buddy/projects/corpus-council/src/corpus_council/core/corpus.py`. Update `ingest_corpus()` to accept `corpus_dir: Path | None = None` parameter. When `corpus_dir` is not None, use it in place of `config.corpus_dir`. Update the type annotation and docstring.
6. Read `/home/buddy/projects/corpus-council/src/corpus_council/cli/main.py`. Replace the `dataclasses.replace(config, corpus_dir=Path(path))` call with `ingest_corpus(config, corpus_dir=Path(path))` directly (removing the `modified_config` variable). Remove the `import dataclasses` if it is no longer used.
7. Read `/home/buddy/projects/corpus-council/src/corpus_council/api/routers/corpus.py`. Replace the `dataclasses.replace(config, corpus_dir=validated_path)` pattern with a direct call to `ingest_corpus(config, corpus_dir=validated_path)`. Remove the `import dataclasses` if it is no longer used.
8. Run all three quality checks and fix any issues before declaring done.

## Verification
- Structural: `grep -n "corpus_dir\|council_dir\|goals_dir\|personas_dir\|goals_manifest_path" /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` shows only `@property` definitions and the migration-error check — no `dataclass` field declarations and no `_resolve_path` calls for those keys.
- Structural: `grep -n "dataclasses.replace" /home/buddy/projects/corpus-council/src/corpus_council/cli/main.py` returns no matches (or only matches unrelated to `corpus_dir`).
- Structural: `grep -n "dataclasses.replace" /home/buddy/projects/corpus-council/src/corpus_council/api/routers/corpus.py` returns no matches.
- Behavioral: `uv run ruff check src/` exits 0.
- Behavioral: `uv run mypy src/` exits 0 with no errors.
- Behavioral: `uv run pytest` (may fail on conftest-dependent tests due to constructor changes — that is expected and will be fixed in Task 00003; however, unit tests for config, store, corpus, goals, council, embeddings, and deliberation should pass).
- Global Constraint: No new packages in `pyproject.toml` — `grep "dependencies" /home/buddy/projects/corpus-council/pyproject.toml` shows the same list as before.
- Global Constraint: No inline prompt strings introduced — `grep -r "\"You are\|'You are\|f\"You" /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` returns no matches.
- Dynamic: `python -c "from corpus_council.core.config import AppConfig; from pathlib import Path; c = AppConfig(llm_provider='x', llm_model='x', embedding_provider='x', embedding_model='x', data_dir=Path('/tmp/test'), chunk_max_size=512, retrieval_top_k=5); assert c.corpus_dir == Path('/tmp/test/corpus'); assert c.council_dir == Path('/tmp/test/council'); assert c.goals_dir == Path('/tmp/test/goals'); assert c.personas_dir == Path('/tmp/test/council'); assert c.goals_manifest_path == Path('/tmp/test/goals_manifest.json'); assert c.chunks_dir == Path('/tmp/test/chunks'); assert c.embeddings_dir == Path('/tmp/test/embeddings'); assert c.users_dir == Path('/tmp/test/users'); print('OK')"` prints `OK`.

## Done When
- [ ] `AppConfig` has no dataclass fields named `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, or `goals_manifest_path`.
- [ ] `AppConfig` has eight `@property` methods returning `Path`: `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`, `chunks_dir`, `embeddings_dir`, `users_dir`.
- [ ] `load_config()` raises `ValueError` with a key-naming message for each of the five removed keys if present in YAML.
- [ ] `ingest_corpus()` accepts an optional `corpus_dir: Path | None = None` parameter.
- [ ] Both `dataclasses.replace(config, corpus_dir=...)` callsites removed.
- [ ] `uv run ruff check src/` exits 0.
- [ ] `uv run mypy src/` exits 0.

## Save Command
```
git add src/corpus_council/core/config.py src/corpus_council/core/corpus.py src/corpus_council/cli/main.py src/corpus_council/api/routers/corpus.py && git commit -m "task-00001: simplify AppConfig — derived path properties, migration errors"
```
