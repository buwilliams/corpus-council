# Task 00000: Extend AppConfig with deliberation_mode and update config.yaml

## Role
programmer

## Objective
Add `deliberation_mode: str = "sequential"` to the `AppConfig` dataclass in `src/corpus_council/core/config.py`, update `load_config()` to read the new field from YAML with a default of `"sequential"` and validate it is one of `"sequential"` or `"consolidated"`, and add the `deliberation_mode: sequential` key with an explanatory comment to `config.yaml`. No other fields, keys, or structural changes are made.

## Context

**Existing file: `src/corpus_council/core/config.py`**

The `AppConfig` dataclass currently has these fields (in order):
```python
@dataclass
class AppConfig:
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    data_dir: Path
    corpus_dir: Path
    council_dir: Path
    templates_dir: Path
    plans_dir: Path
    chunk_max_size: int
    retrieval_top_k: int
    chroma_collection: str = "corpus"
```

`load_config()` reads from YAML and returns a fully constructed `AppConfig`. The function uses `_require_str`, `_require_int`, `_require_dict` helpers for required fields, and `data.get(key, default)` for optional fields. The new `deliberation_mode` field is optional (defaults to `"sequential"`) and must be read with `data.get("deliberation_mode", "sequential")`. After reading it, validate it is one of `{"sequential", "consolidated"}` and raise `ValueError` with a clear message if not.

The field must be added to `AppConfig` with a default of `"sequential"` so existing code that constructs `AppConfig` without this field (like the fixture in `tests/conftest.py`) continues to work.

**Existing file: `config.yaml`** (at project root `/home/buddy/projects/corpus-council/config.yaml`)

Current contents end with:
```yaml
chroma_collection: corpus
```

Add after that line:
```yaml
# Deliberation mode: "sequential" (default, 2N+1 LLM calls) or "consolidated" (2 LLM calls)
deliberation_mode: sequential
```

**Tech stack:** Python 3.12+, PyYAML, `uv` for all commands. All new code must pass `mypy src/corpus_council/core/` under `strict = true`.

**Global constraint:** `deliberation_mode` is the only new config key. No other fields may be added to `AppConfig` or `config.yaml`.

## Steps

1. Open `src/corpus_council/core/config.py`. Add `deliberation_mode: str = "sequential"` as the last field of `AppConfig` (after `chroma_collection: str = "corpus"`).
2. In `load_config()`, after the `chroma_collection` block, read the new field:
   ```python
   deliberation_mode_raw = data.get("deliberation_mode", "sequential")
   if not isinstance(deliberation_mode_raw, str):
       raise ValueError(
           f"Config key 'deliberation_mode' must be a string, got {type(deliberation_mode_raw).__name__!r}"
       )
   if deliberation_mode_raw not in {"sequential", "consolidated"}:
       raise ValueError(
           f"Config key 'deliberation_mode' must be 'sequential' or 'consolidated', "
           f"got {deliberation_mode_raw!r}"
       )
   deliberation_mode: str = deliberation_mode_raw
   ```
3. Pass `deliberation_mode=deliberation_mode` in the `AppConfig(...)` constructor call at the end of `load_config()`.
4. Open `config.yaml`. Add the comment and `deliberation_mode: sequential` line after `chroma_collection: corpus`.

## Verification

- Structural:
  - `src/corpus_council/core/config.py` exports `AppConfig` with field `deliberation_mode: str`
  - `config.yaml` contains the string `deliberation_mode: sequential`
  - `grep -n 'deliberation_mode' /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` returns at least 2 matches (field definition and assignment in constructor call)
  - `grep -n 'any\|@ts-ignore' /home/buddy/projects/corpus-council/src/corpus_council/core/config.py` returns no Python `Any` typed as `any` (note: `Any` from typing is used in existing code for `dict[str, Any]` — the constraint is no TypeScript-style issues; verify mypy passes instead)
- Behavioral:
  - `uv run mypy src/corpus_council/core/config.py` exits 0
  - `uv run ruff check src/corpus_council/core/config.py` exits 0
  - `uv run ruff format --check src/corpus_council/core/config.py` exits 0
  - `uv run pytest tests/unit/test_config.py` exits 0 (existing tests must still pass)
- Global constraint — only one new config key:
  - `grep -c 'deliberation_mode' /home/buddy/projects/corpus-council/config.yaml` outputs `2` (comment line + value line) or `1` (value line only — acceptable); no other new top-level keys
- Dynamic:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run python -c "
  from corpus_council.core.config import load_config
  cfg = load_config('config.yaml')
  assert cfg.deliberation_mode == 'sequential', f'Expected sequential, got {cfg.deliberation_mode!r}'
  print('OK: deliberation_mode =', cfg.deliberation_mode)
  "
  ```

## Done When
- [ ] `AppConfig` has `deliberation_mode: str = "sequential"` as the last field
- [ ] `load_config()` reads `deliberation_mode` from YAML, defaults to `"sequential"`, and raises `ValueError` for invalid values
- [ ] `config.yaml` contains `deliberation_mode: sequential`
- [ ] `uv run mypy src/corpus_council/core/config.py` exits 0
- [ ] `uv run pytest tests/unit/test_config.py` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/config.py config.yaml && git commit -m "task-00000: add deliberation_mode field to AppConfig and config.yaml"
```
