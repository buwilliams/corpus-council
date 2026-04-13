# Task 00004: Write New Config and Store Tests

## Role
tester

## Objective
Write new test coverage in `tests/unit/test_config.py` and `tests/unit/test_store.py` that specifically covers: the migration-error detection for all five removed keys, all eight derived `@property` accessors on `AppConfig`, and `FileStore` initialized with a `users_dir`-style path. These tests must not exist yet (they were deleted or never existed before this task).

## Context
This task depends on Task 00001 (AppConfig simplified), Task 00002 (FileStore updated), and Task 00003 (existing tests updated). By the time this task runs, the existing tests should be green.

**Migration-error tests** — `load_config()` raises `ValueError` for each of the five removed keys when present in a YAML config. Each removed key needs its own test (or a parametrized test). The error message must name the offending key.

Removed keys: `corpus_dir`, `council_dir`, `goals_dir`, `personas_dir`, `goals_manifest_path`.

Example test structure:
```python
@pytest.mark.parametrize("key", [
    "corpus_dir",
    "council_dir",
    "goals_dir",
    "personas_dir",
    "goals_manifest_path",
])
def test_load_config_raises_on_removed_key(tmp_path: Path, key: str) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: anthropic\n"
        "  model: claude-3-5-haiku-20241022\n"
        "embedding:\n"
        "  provider: sentence-transformers\n"
        "  model: all-MiniLM-L6-v2\n"
        "data_dir: data\n"
        f"{key}: some_value\n"
        "chunking:\n"
        "  max_size: 512\n"
        "retrieval:\n"
        "  top_k: 5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=key):
        load_config(config_file)
```

**Derived-path tests** — verify all eight `@property` accessors:
- `corpus_dir` → `data_dir / "corpus"`
- `council_dir` → `data_dir / "council"`
- `goals_dir` → `data_dir / "goals"`
- `personas_dir` → `data_dir / "council"`
- `goals_manifest_path` → `data_dir / "goals_manifest.json"`
- `chunks_dir` → `data_dir / "chunks"`
- `embeddings_dir` → `data_dir / "embeddings"`
- `users_dir` → `data_dir / "users"`

Write one test that loads a minimal YAML and asserts all eight paths; also write or confirm tests that directly instantiate `AppConfig` and check each property.

**FileStore + users_dir test** — write a test that:
1. Creates `FileStore(tmp_path / "users")` (simulating `config.users_dir`).
2. Calls `store.append_jsonl(store.goal_messages_path("abc123ef", "test-goal", "conv-001"), {"msg": "hello"})`.
3. Asserts the file was written under `tmp_path / "users" / "ab" / "c1" / "abc123ef" / ...`.
4. Reads it back and asserts the content matches.
Uses `tmp_path` exclusively — no mocks.

**Import requirements**: `from corpus_council.core.config import AppConfig, load_config` and `from corpus_council.core.store import FileStore`.

**Test framework**: pytest, no external test libraries. Use `tmp_path` for all filesystem operations.

**File locations**:
- `/home/buddy/projects/corpus-council/tests/unit/test_config.py` — append new tests
- `/home/buddy/projects/corpus-council/tests/unit/test_store.py` — append new tests

## Steps
1. Read `tests/unit/test_config.py` and `tests/unit/test_store.py` in full (post Task 00003 state).
2. Add to `tests/unit/test_config.py`:
   a. A parametrized test `test_load_config_raises_on_removed_key` covering all five keys; assert `ValueError` with the key name in the message.
   b. A test `test_all_derived_paths_resolve_from_data_dir` that loads a minimal YAML with `data_dir: testroot` and asserts all eight properties equal `(tmp_path / "testroot" / <subdir>).resolve()`.
   c. A test `test_personas_dir_equals_council_dir` that asserts `config.personas_dir == config.council_dir`.
   d. A test `test_chunks_dir_and_embeddings_dir_and_users_dir_derived` that directly constructs `AppConfig` with a known `data_dir` and asserts `chunks_dir`, `embeddings_dir`, and `users_dir` values.
3. Add to `tests/unit/test_store.py`:
   a. A test `test_filestore_with_users_dir_writes_to_correct_path` that initializes `FileStore(tmp_path / "users")`, appends a JSONL record at `store.goal_messages_path("abc123ef", "test-goal", "conv-001")`, and asserts the file exists at `tmp_path / "users" / "ab" / "c1" / "abc123ef" / "goals" / "test-goal" / "conv-001" / "messages.jsonl"`.
   b. A test `test_filestore_users_dir_base_read_back` that writes and reads back a record through the store and asserts content equality.
4. Run `uv run pytest` and confirm all new tests pass.

## Verification
- Structural: `grep -n "test_load_config_raises_on_removed_key" /home/buddy/projects/corpus-council/tests/unit/test_config.py` returns a match.
- Structural: `grep -n "test_all_derived_paths_resolve_from_data_dir\|test_chunks_dir_and_embeddings_dir" /home/buddy/projects/corpus-council/tests/unit/test_config.py` returns matches.
- Structural: `grep -n "test_filestore_with_users_dir" /home/buddy/projects/corpus-council/tests/unit/test_store.py` returns a match.
- Structural: `grep -n "mock\|patch\|MagicMock" /home/buddy/projects/corpus-council/tests/unit/test_store.py` returns no new matches related to file I/O (hard constraint: no mocks for filesystem).
- Behavioral: `uv run pytest tests/unit/test_config.py -v` exits 0 with all parametrized migration-error tests shown as passed.
- Behavioral: `uv run pytest tests/unit/test_store.py -v` exits 0.
- Behavioral: `uv run pytest` exits 0.
- Global Constraint: No new packages in `pyproject.toml`.
- Dynamic: `uv run pytest tests/unit/test_config.py::test_load_config_raises_on_removed_key -v` exits 0 and shows 5 parametrized variants all passed.

## Done When
- [ ] Parametrized `test_load_config_raises_on_removed_key` covers all five removed keys and asserts `ValueError` with key name in message.
- [ ] `test_all_derived_paths_resolve_from_data_dir` covers all eight derived properties.
- [ ] `test_filestore_with_users_dir_writes_to_correct_path` uses `tmp_path / "users"` as base and asserts correct file location.
- [ ] No mocks of filesystem operations in store tests.
- [ ] `uv run pytest` exits 0.

## Save Command
```
git add tests/unit/test_config.py tests/unit/test_store.py && git commit -m "task-00004: add tests for migration errors, derived paths, and FileStore users_dir init"
```
