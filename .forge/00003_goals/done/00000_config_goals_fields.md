# Task 00000: Add goals_dir, personas_dir, and goals_manifest_path to AppConfig

## Role
programmer

## Objective
Extend `src/corpus_council/core/config.py` and `config.yaml` so that `AppConfig` includes three new fields: `goals_dir: Path`, `personas_dir: Path`, and `goals_manifest_path: Path`. These fields must be read from `config.yaml` with sensible defaults (`goals`, `council`, and `goals_manifest.json` respectively). All three must be resolved as absolute paths relative to the config file's directory, consistent with how existing path fields are handled.

## Context
The project goal is to replace the hardcoded collection/conversation mode distinction with a goals model. Every `AppConfig`-consuming module will need these three new paths. They must be added before any other task can reference them.

**Current `AppConfig` dataclass** is in `/home/buddy/projects/corpus-council/src/corpus_council/core/config.py`. It already has fields: `llm_provider`, `llm_model`, `embedding_provider`, `embedding_model`, `data_dir`, `corpus_dir`, `council_dir`, `templates_dir`, `plans_dir`, `chunk_max_size`, `retrieval_top_k`, `chroma_collection`, `deliberation_mode`.

**`load_config` function** in the same file uses `_resolve_path(config_dir, value)` for path fields and `data.get("field_name", "default")` for optional fields with defaults. The same pattern must be used for the three new fields.

**`config.yaml`** is at `/home/buddy/projects/corpus-council/config.yaml`. It currently has no `goals_dir`, `personas_dir`, or `goals_manifest_path` keys — these must be added with their default values.

**Existing tests that construct `AppConfig` directly** (e.g., `tests/conftest.py`, `tests/unit/test_council.py`) will need to be updated to pass the three new fields, or the fields must have defaults so existing instantiations continue to compile. Since `AppConfig` is a `@dataclass`, adding fields without defaults after fields with defaults is a Python error. Use `field(default=...)` from `dataclasses` or give default values in the dataclass definition. The safest approach is to give all three new fields default `Path` values (matching the string defaults) so existing test code that constructs `AppConfig` without them continues to work — but note: the defaults are just fallback strings; `load_config` must still resolve them relative to the config directory.

**No new external dependencies.** `dataclasses`, `pathlib.Path`, and `yaml` are already in use.

Tech stack: Python 3.12, `dataclasses`, `pathlib`, `PyYAML`.

## Steps
1. Open `/home/buddy/projects/corpus-council/src/corpus_council/core/config.py`.
2. Add three new fields to the `AppConfig` dataclass after the existing path fields (`plans_dir`), before `chunk_max_size`. Use `dataclasses.field` with `default_factory` pointing to a sensible default path, or use a sentinel default. Because `AppConfig` uses positional dataclass fields today (no defaults), the safest approach is to add defaults at the end of the field list so existing test instantiations (which use keyword arguments already) do not break. Add:
   ```python
   goals_dir: Path = dataclasses.field(default_factory=lambda: Path("goals"))
   personas_dir: Path = dataclasses.field(default_factory=lambda: Path("council"))
   goals_manifest_path: Path = dataclasses.field(default_factory=lambda: Path("goals_manifest.json"))
   ```
   These defaults are placeholder non-absolute paths; `load_config` will always resolve them to absolute paths.
3. In `load_config`, after the existing path field resolutions, add:
   ```python
   goals_dir = _resolve_path(config_dir, data.get("goals_dir", "goals"))
   personas_dir = _resolve_path(config_dir, data.get("personas_dir", "council"))
   goals_manifest_path = _resolve_path(config_dir, data.get("goals_manifest_path", "goals_manifest.json"))
   ```
4. Pass the three new fields in the `AppConfig(...)` constructor call at the bottom of `load_config`.
5. Add `goals_dir`, `personas_dir`, and `goals_manifest_path` to the `__all__` export list if `AppConfig` is listed there (it already is via `__all__ = ["AppConfig", "load_config"]` — no change needed for `__all__`).
6. Open `/home/buddy/projects/corpus-council/config.yaml`. Add the three new keys with their defaults:
   ```yaml
   goals_dir: goals
   personas_dir: council
   goals_manifest_path: goals_manifest.json
   ```
7. Update `tests/conftest.py` fixture `test_config` to pass the three new fields to `AppConfig(...)` so the fixture still constructs a fully-specified config. Point `goals_dir` at a `tmp_path / "goals"` dir (create it), `personas_dir` at the existing `council_dir`, and `goals_manifest_path` at `tmp_path / "goals_manifest.json"`.
8. Update any other test files that directly instantiate `AppConfig` (e.g., `tests/unit/test_council.py`, `tests/unit/test_config.py`) to include the three new fields, or verify that the dataclass defaults cover them.
9. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest` and fix any errors.

## Verification
- Structural: `src/corpus_council/core/config.py` contains fields `goals_dir: Path`, `personas_dir: Path`, `goals_manifest_path: Path` in `AppConfig`
- Structural: `load_config` resolves all three from `config.yaml` using `_resolve_path` with the correct defaults
- Structural: `config.yaml` contains `goals_dir`, `personas_dir`, and `goals_manifest_path` keys
- Structural: `tests/conftest.py` passes all three fields when constructing `AppConfig`
- Behavioral: `uv run mypy src/` exits 0 (strict mode — all fields typed correctly)
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run pytest` exits 0
- Constraint (no hardcoded behavioral rules in Python source): Grep `src/corpus_council/` for `"collection"` or `"conversation"` routing strings — this task must not introduce any
- Constraint (no new external packages): `pyproject.toml` dependencies section is unchanged
- Dynamic: `uv run python -c "from corpus_council.core.config import load_config; from pathlib import Path; c = load_config(Path('config.yaml')); print(c.goals_dir, c.personas_dir, c.goals_manifest_path)"` prints three absolute paths without error

## Done When
- [ ] `AppConfig` has `goals_dir`, `personas_dir`, `goals_manifest_path` fields with correct types
- [ ] `load_config` reads these from `config.yaml` with correct defaults
- [ ] `config.yaml` declares these three keys
- [ ] All existing tests still pass (`uv run pytest` exits 0)
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/config.py config.yaml tests/conftest.py tests/unit/test_council.py tests/unit/test_config.py && git commit -m "task-00000: add goals_dir, personas_dir, goals_manifest_path to AppConfig"
```
