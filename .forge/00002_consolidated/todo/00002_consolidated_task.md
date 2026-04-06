# Task 00002: Implement run_consolidated_deliberation() in consolidated.py

## Role
programmer

## Objective
Create `src/corpus_council/core/consolidated.py` implementing `run_consolidated_deliberation(user_message, corpus_chunks, members, llm) -> DeliberationResult`. The function makes exactly 2 `llm.call()` invocations (first `"council_consolidated"`, then `"evaluator_consolidated"`), parses `ESCALATION:` lines from the council output, builds a `deliberation_log` as `list[MemberLog]`, and returns a `DeliberationResult`. No new return types are introduced.

## Context

**Task 00000** added `deliberation_mode` to `AppConfig`. **Task 00001** created `templates/council_consolidated.md` and `templates/evaluator_consolidated.md`.

**Types to import from existing modules:**

From `src/corpus_council/core/deliberation.py`:
```python
@dataclass
class MemberLog:
    member_name: str
    position: int
    response: str
    escalation_triggered: bool

@dataclass
class DeliberationResult:
    final_response: str
    deliberation_log: list[MemberLog]
    escalation_triggered: bool
    escalating_member: str | None
```

The `_format_chunks()` helper in `deliberation.py` is module-private; do not import it. Implement an equivalent inline or as a private helper in `consolidated.py`.

From `src/corpus_council/core/council.py`:
```python
@dataclass
class CouncilMember:
    name: str
    persona: str
    primary_lens: str
    position: int
    role_type: str
    escalation_rule: str
    body: str
    source_file: str
```

From `src/corpus_council/core/llm.py`:
```python
class LLMClient:
    def call(self, template_name: str, context: dict[str, Any]) -> str: ...
    def render_template(self, template_name: str, context: dict[str, Any]) -> str: ...
```

From `src/corpus_council/core/retrieval.py`:
```python
@dataclass
class ChunkResult:
    text: str
    source_file: str
    chunk_index: int
```

**Council template output format** (from Task 00001):
```
=== MEMBER: Alice ===
<member's response text>
ESCALATION: NONE
=== END MEMBER ===

=== MEMBER: Bob ===
<member's response text>
ESCALATION: concern text
=== END MEMBER ===
```

**Parsing algorithm:**
1. Split the council call output on `"=== MEMBER:"` — the first element (index 0) is empty or preamble; elements 1+ are member blocks
2. For each member block:
   - Extract member name: first line up to `" ==="`
   - Extract `ESCALATION:` line: look for a line starting with `ESCALATION:` in the block
   - Determine `escalation_triggered`: True if the escalation value (after `ESCALATION: `) is not `"NONE"`
   - Identify the `CouncilMember` by name match to get the `position` integer
   - Build a `MemberLog(member_name=name, position=pos, response=response_text, escalation_triggered=...)`
3. Build `escalation_summary`: join non-`NONE` escalation lines with `"\n"`
4. Set `escalation_triggered` = True if any member's escalation was non-`NONE`
5. Set `escalating_member` = name of first member with non-`NONE` escalation (or `None`)

**Exactly 2 `llm.call()` invocations:**
```python
council_output = llm.call("council_consolidated", {
    "members": members,
    "user_message": user_message,
    "corpus_chunks": corpus_text,
})
# ... parse council_output ...
final_response = llm.call("evaluator_consolidated", {
    "user_message": user_message,
    "council_responses": council_output,
    "escalation_summary": escalation_summary,
})
```

No other `llm.call()` or `llm.render_template()` calls may appear in this function.

**Global constraints:**
- No inline prompt strings — both LLM calls must use `llm.call(template_name, context)`
- No hardcoded persona descriptions or escalation rules in Python
- Return type must be `DeliberationResult` — the identical dataclass from `deliberation.py`
- Exactly 2 `llm.call()` invocations — invariant regardless of member count or escalation count
- All new code must pass `mypy src/corpus_council/core/` under `strict = true`
- No new Python packages

**Pattern to follow:** `src/corpus_council/core/deliberation.py` for the overall structure. Use `from __future__ import annotations` at the top. Export only the public function via `__all__`.

## Steps

1. Create `src/corpus_council/core/consolidated.py` with:
   - `from __future__ import annotations` at top
   - Imports: `from typing import Any`, `from .council import CouncilMember`, `from .deliberation import DeliberationResult, MemberLog`, `from .llm import LLMClient`, `from .retrieval import ChunkResult`
   - Private helper `_format_chunks(chunks: list[ChunkResult]) -> str` — same logic as in `deliberation.py`
   - Private helper `_parse_council_output(council_output: str, members: list[CouncilMember]) -> list[MemberLog]` — implements the parsing algorithm above
   - Private helper `_build_escalation_summary(log: list[MemberLog], raw_escalations: dict[str, str]) -> str` — or inline escalation summary construction
   - Public function `run_consolidated_deliberation(user_message: str, corpus_chunks: list[ChunkResult], members: list[CouncilMember], llm: LLMClient) -> DeliberationResult`

2. In `run_consolidated_deliberation()`:
   - Call `_format_chunks(corpus_chunks)` to get `corpus_text: str`
   - Make call 1: `council_output = llm.call("council_consolidated", {"members": members, "user_message": user_message, "corpus_chunks": corpus_text})`
   - Parse council output to get `deliberation_log: list[MemberLog]` and `escalation_summary: str`
   - Determine `escalation_triggered: bool` and `escalating_member: str | None`
   - Make call 2: `final_response = llm.call("evaluator_consolidated", {"user_message": user_message, "council_responses": council_output, "escalation_summary": escalation_summary})`
   - Return `DeliberationResult(final_response=final_response, deliberation_log=deliberation_log, escalation_triggered=escalation_triggered, escalating_member=escalating_member)`

3. Add `__all__ = ["run_consolidated_deliberation"]` at the bottom.

## Verification

- Structural:
  - File `src/corpus_council/core/consolidated.py` exists
  - `grep -n 'def run_consolidated_deliberation' /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` returns a match
  - `grep -cn 'llm\.call(' /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` outputs exactly `2` (two call sites)
  - `grep -n 'f".*\{' /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` returns no f-string prompts used as LLM input (f-strings for error messages or formatting are acceptable, but no f-string passed directly to `llm.call()`)
  - `grep -n 'DeliberationResult\|MemberLog' /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` shows imports of both types
- Global constraints:
  - No inline prompt strings: confirm `llm.call()` is always called with a template name string literal, never an f-string or computed prompt
  - `grep -n 'run_deliberation\|from .deliberation import run_deliberation' /home/buddy/projects/corpus-council/src/corpus_council/core/consolidated.py` returns no matches (the sequential pipeline is not called or imported)
- Behavioral:
  - `uv run mypy src/corpus_council/core/consolidated.py` exits 0
  - `uv run ruff check src/corpus_council/core/consolidated.py` exits 0
  - `uv run ruff format --check src/corpus_council/core/consolidated.py` exits 0
- Dynamic: verify the function is importable and has the correct signature:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run python -c "
  from corpus_council.core.consolidated import run_consolidated_deliberation
  import inspect
  sig = inspect.signature(run_consolidated_deliberation)
  params = list(sig.parameters.keys())
  assert 'user_message' in params, 'missing user_message'
  assert 'corpus_chunks' in params, 'missing corpus_chunks'
  assert 'members' in params, 'missing members'
  assert 'llm' in params, 'missing llm'
  print('run_consolidated_deliberation signature OK:', params)
  "
  ```

## Done When
- [ ] `src/corpus_council/core/consolidated.py` exists and exports `run_consolidated_deliberation`
- [ ] The function makes exactly 2 `llm.call()` invocations
- [ ] The function returns `DeliberationResult` (same type as `run_deliberation()`)
- [ ] Escalation parsing correctly identifies non-`NONE` escalation lines and sets `escalation_triggered` and `escalating_member`
- [ ] `uv run mypy src/corpus_council/core/consolidated.py` exits 0
- [ ] `uv run ruff check src/corpus_council/core/consolidated.py` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/consolidated.py && git commit -m "task-00002: implement run_consolidated_deliberation in consolidated.py"
```
