# Task 00003: Update conftest.py and Existing Tests

## Role
tester

## Objective
Update `tests/conftest.py` to construct `AppConfig` without the five removed dataclass fields (`corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`), so the `test_config` fixture works with the simplified `AppConfig`. Update `tests/unit/test_config.py` to remove tests that assert on the old YAML-configurable behavior and replace them with correct assertions for the new derived-path model. Ensure all existing tests pass after these changes.

## Context
This task depends on Task 00001 (AppConfig simplified) and Task 00002 (FileStore updated).

**`tests/conftest.py`** — the `test_config` fixture currently constructs:
```python
return AppConfig(
    llm_provider="anthropic",
    llm_model="claude-haiku-4-5-20251001",
    embedding_provider="sentence-transformers",
    embedding_model="all-MiniLM-L6-v2",
    data_dir=data_dir,
    corpus_dir=corpus_dir,
    council_dir=council_dir,
    chunk_max_size=512,
    retrieval_top_k=3,
    chroma_collection="test_corpus",
    goals_dir=goals_dir,
    personas_dir=council_dir,
    goals_manifest_path=tmp_path / "goals_manifest.json",
)
```
After Task 00001, `AppConfig` no longer has these five fields. The constructor must become:
```python
return AppConfig(
    llm_provider="anthropic",
    llm_model="claude-haiku-4-5-20251001",
    embedding_provider="sentence-transformers",
    embedding_model="all-MiniLM-L6-v2",
    data_dir=data_dir,
    chunk_max_size=512,
    retrieval_top_k=3,
    chroma_collection="test_corpus",
)
```

**But wait** — `test_config` relies on `data_dir = tmp_path / "data"` (from the `data_dir` fixture), while `corpus_dir`, `council_dir`, and `goals_dir` fixtures create directories at `tmp_path / "corpus"`, `tmp_path / "council"`, `tmp_path / "goals"`. After the simplification, `AppConfig.corpus_dir` returns `data_dir / "corpus"` = `tmp_path / "data" / "corpus"`, NOT `tmp_path / "corpus"`.

This means the `corpus_dir`, `council_dir`, and `goals_dir` fixtures must be updated to create their files under `data_dir` (i.e., `tmp_path / "data" / "corpus"`, `tmp_path / "data" / "council"`, etc.) OR the `test_config` fixture must set `data_dir = tmp_path` so that `data_dir / "corpus"` = `tmp_path / "corpus"`.

**Recommended approach**: Change the `data_dir` fixture to return `tmp_path` directly (not `tmp_path / "data"`). Then `AppConfig(data_dir=tmp_path, ...)` gives:
- `corpus_dir` = `tmp_path / "corpus"` ✓ (matches `corpus_dir` fixture)
- `council_dir` = `tmp_path / "council"` ✓ (matches `council_dir` fixture)
- `goals_dir` = `tmp_path / "goals"` ✓ (matches `goals_dir` fixture)
- `goals_manifest_path` = `tmp_path / "goals_manifest.json"` ✓ (matches where `process_goals` writes it in the `goals_dir` fixture)
- `users_dir` = `tmp_path / "users"` ✓

The `goals_dir` fixture currently writes `goals_manifest.json` to `tmp_path / "goals_manifest.json"` — that path matches `goals_manifest_path` when `data_dir = tmp_path`.

Also update `file_store` fixture: was `FileStore(test_config.data_dir)`, Task 00002 changed it to `FileStore(test_config.users_dir)` — ensure this is consistent.

Integration tests that set `app_module.store = FileStore(test_config.data_dir)` must be updated to `FileStore(test_config.users_dir)` (Task 00002 covers those files, but double-check consistency here).

**`tests/unit/test_config.py`** — these tests need updating:

1. `test_load_config_returns_all_required_fields` — uses the real `config.yaml` which after Task 00005 will no longer have the five old keys. Currently it asserts `isinstance(config.corpus_dir, Path)` and `isinstance(config.council_dir, Path)` — these still work with properties, but the real config.yaml must be updated first (Task 00005). For now, ensure the test continues to work with a `config.yaml` that lacks the five old keys.

2. `test_load_config_resolves_paths_relative_to_config_file` — currently only checks `data_dir`; no change needed.

3. `test_load_config_includes_goals_fields` — writes a YAML with `goals_dir`, `personas_dir`, `goals_manifest_path` keys and expects them to be read. After Task 00001, this YAML will trigger `ValueError`. This test must be REPLACED with one that:
   - Writes a minimal YAML (no five old keys)
   - Asserts `config.goals_dir == (tmp_path / "mydata" / "goals").resolve()`
   - Asserts `config.personas_dir == (tmp_path / "mydata" / "council").resolve()`
   - Asserts `config.goals_manifest_path == (tmp_path / "mydata" / "goals_manifest.json").resolve()`

4. `test_load_config_goals_fields_use_defaults` — asserts defaults relative to config file dir, not `data_dir`. After the change, defaults come from `data_dir`. This test must be REPLACED with one that asserts the derived paths relative to `data_dir`.

**File**: `/home/buddy/projects/corpus-council/tests/unit/test_config.py`

## Steps
1. Read `tests/conftest.py`, `tests/unit/test_config.py`, `tests/unit/test_store.py`.
2. Update `conftest.py`:
   a. Change the `data_dir` fixture to return `tmp_path` (not `tmp_path / "data"`).
   b. Remove the five removed fields from the `AppConfig(...)` constructor in `test_config`.
   c. If `file_store` fixture uses `test_config.data_dir`, update to `test_config.users_dir`.
3. Update `tests/unit/test_config.py`:
   a. Remove `test_load_config_includes_goals_fields` (it tests behavior that no longer exists). Replace it with `test_derived_paths_resolve_from_data_dir` that writes a minimal YAML with `data_dir: mydata` and asserts all derived paths.
   b. Remove `test_load_config_goals_fields_use_defaults`. Replace with `test_derived_paths_use_data_dir_by_convention` that confirms all eight `@property` paths derive from `data_dir`.
   c. Keep `test_load_config_returns_all_required_fields`, `test_load_config_resolves_paths_relative_to_config_file`, `test_load_config_raises_file_not_found_for_missing_file`, and `test_load_config_raises_on_missing_required_key` unchanged.
4. Run `uv run pytest` to confirm all tests pass. Fix any remaining failures.

## Verification
- Structural: `grep -n "corpus_dir=\|council_dir=\|goals_dir=\|personas_dir=\|goals_manifest_path=" /home/buddy/projects/corpus-council/tests/conftest.py` returns no matches (the removed fields are gone from the constructor call).
- Structural: The `data_dir` fixture in `conftest.py` returns `tmp_path` (not `tmp_path / "data"`).
- Structural: `tests/unit/test_config.py` no longer contains `test_load_config_includes_goals_fields` or `test_load_config_goals_fields_use_defaults`.
- Behavioral: `uv run pytest tests/unit/test_config.py` exits 0.
- Behavioral: `uv run pytest tests/unit/test_store.py` exits 0.
- Behavioral: `uv run pytest` exits 0 (all tests).
- Global Constraint: No new packages in `pyproject.toml`.
- Global Constraint: No mocks of filesystem operations in store tests — `grep -n "mock\|patch\|MagicMock" /home/buddy/projects/corpus-council/tests/unit/test_store.py` returns no matches relating to file I/O.
- Dynamic: `uv run pytest tests/unit/test_config.py tests/unit/test_store.py -v` exits 0 and outputs `passed` for all test functions.

## Done When
- [ ] `conftest.py` `data_dir` fixture returns `tmp_path`.
- [ ] `conftest.py` `test_config` fixture does not pass the five removed fields to `AppConfig`.
- [ ] `tests/unit/test_config.py` does not contain tests asserting the old YAML-key behavior.
- [ ] `tests/unit/test_config.py` contains tests asserting derived paths from `data_dir`.
- [ ] `uv run pytest` exits 0.

## Save Command
```
git add tests/conftest.py tests/unit/test_config.py && git commit -m "task-00003: update conftest and test_config for simplified AppConfig"
```
