# Task 00006: Write unit tests for consolidated.py

## Role
tester

## Objective
Create `tests/unit/test_consolidated.py` with five focused unit tests for the consolidated deliberation path: template rendering (both templates with real Jinja2 — no mocking of template rendering), exact-2-call count verification, `DeliberationResult` return type verification, and escalation parsing verification. LLM HTTP calls (i.e., `LLMClient._call_anthropic`) may be stubbed at the method level only — template rendering must always be real.

## Context

**Tasks completed before this task:**
- Task 00000: `AppConfig` has `deliberation_mode: str = "sequential"`
- Task 00001: `templates/council_consolidated.md` and `templates/evaluator_consolidated.md` exist
- Task 00002: `src/corpus_council/core/consolidated.py` exports `run_consolidated_deliberation()`
- Task 00003: `run_conversation()` dispatches on `mode`

**Test infrastructure (from `tests/conftest.py`):**

The `test_config` fixture provides an `AppConfig` with all paths pointing at `tmp_path`. The `templates_dir` fixture copies all real template files from `templates/` to `tmp_path/templates/`. The `council_dir` fixture creates 3 council members. These fixtures are all available in unit tests.

Key fixture signatures:
```python
@pytest.fixture
def test_config(tmp_path, corpus_dir, council_dir, plans_dir, templates_dir, data_dir) -> AppConfig: ...
@pytest.fixture
def templates_dir(tmp_path) -> Path:  # copies all files from templates/
@pytest.fixture
def council_dir(tmp_path) -> Path:  # 3 members: Final Synthesizer (pos 1), Domain Analyst (pos 2), Adversarial Critic (pos 3)
```

**Types and signatures to use:**

```python
from corpus_council.core.consolidated import run_consolidated_deliberation
from corpus_council.core.deliberation import DeliberationResult, MemberLog
from corpus_council.core.council import CouncilMember
from corpus_council.core.llm import LLMClient
from corpus_council.core.retrieval import ChunkResult
```

`LLMClient.call(template_name, context)` calls `self.render_template(template_name, context)` then `self._call_anthropic(rendered_prompt)`. To stub only the LLM call (not template rendering), patch `LLMClient._call_anthropic` or patch `LLMClient.call` directly. Per the constraint, template rendering must NOT be mocked — only the actual network call.

**Council template output format** (from Task 00001):
```
=== MEMBER: Domain Analyst ===
Some analytical response here.
ESCALATION: NONE
=== END MEMBER ===

=== MEMBER: Adversarial Critic ===
Some critical response here.
ESCALATION: NONE
=== END MEMBER ===
```

**Escalation format when triggered:**
```
=== MEMBER: Domain Analyst ===
This is out of scope entirely.
ESCALATION: Response is out of scope
=== END MEMBER ===
```

**Global constraints enforced in tests:**
- No mocking of: corpus file loading, council persona loading, `FileStore` file I/O, ChromaDB, prompt template rendering
- LLM HTTP calls may be stubbed via `monkeypatch` on `LLMClient.call` (the full method, not `render_template`)
- Tests that use real LLM calls must be marked `@pytest.mark.llm` and skipped without `ANTHROPIC_API_KEY`
- These unit tests do NOT carry the `llm` marker — they stub the LLM call layer

**Pattern for stubbing LLM calls:**

Use `monkeypatch.setattr` to replace `LLMClient.call`. Track calls with a list:
```python
call_log: list[tuple[str, dict]] = []

def fake_call(self, template_name: str, context: dict) -> str:
    call_log.append((template_name, context))
    if template_name == "council_consolidated":
        return (
            "=== MEMBER: Domain Analyst ===\n"
            "Some analytical response.\n"
            "ESCALATION: NONE\n"
            "=== END MEMBER ===\n\n"
            "=== MEMBER: Final Synthesizer ===\n"
            "Synthesis here.\n"
            "ESCALATION: NONE\n"
            "=== END MEMBER ===\n"
        )
    return "Final evaluated response."

monkeypatch.setattr(LLMClient, "call", fake_call)
```

Note: the stub must return a council output string that matches the parser's expected format (the `=== MEMBER: ===` delimiter pattern from Task 00001).

**Template rendering tests** — use `llm.render_template()` (the real method, no stub):
```python
llm = LLMClient(test_config)
rendered = llm.render_template("council_consolidated", {
    "members": members,
    "user_message": "What is the impact of AI?",
    "corpus_chunks": "AI is rapidly evolving."
})
assert "Domain Analyst" in rendered
assert "Adversarial Critic" in rendered
```

## Steps

1. Create `tests/unit/test_consolidated.py`.

2. Implement `test_council_consolidated_template_renders_all_personas`:
   - Use `test_config` and `council_dir` fixtures
   - Load council members from `council_dir` via `load_council(test_config)`
   - Instantiate `LLMClient(test_config)` (no stub — real template rendering)
   - Call `llm.render_template("council_consolidated", {"members": members, "user_message": "...", "corpus_chunks": "..."})`
   - Assert all 3 member names appear in the rendered output: "Final Synthesizer", "Domain Analyst", "Adversarial Critic"
   - Assert the string `"ESCALATION:"` appears in the output

3. Implement `test_evaluator_consolidated_template_renders_inputs`:
   - Instantiate `LLMClient(test_config)` (no stub)
   - Call `llm.render_template("evaluator_consolidated", {"user_message": "Test question", "council_responses": "=== MEMBER: Alice ===\nResponse\nESCALATION: NONE\n=== END MEMBER ===", "escalation_summary": "Alice: concern here"})`
   - Assert `"Test question"` appears in output
   - Assert `"=== MEMBER: Alice ==="` or `"council_responses"` content appears (the template renders the variable)
   - Assert `"concern here"` appears in output (escalation_summary is rendered)

4. Implement `test_run_consolidated_deliberation_makes_exactly_two_calls`:
   - Use `test_config`, `council_dir` fixtures
   - Load members with `load_council(test_config)`
   - Stub `LLMClient.call` with `monkeypatch` tracking calls to `call_log`
   - Call `run_consolidated_deliberation("test message", [], members, llm)`
   - Assert `len(call_log) == 2`
   - Assert `call_log[0][0] == "council_consolidated"`
   - Assert `call_log[1][0] == "evaluator_consolidated"`

5. Implement `test_run_consolidated_deliberation_returns_deliberation_result`:
   - Stub `LLMClient.call` to return known strings
   - Call `run_consolidated_deliberation(...)` with 2-member subset from fixture
   - Assert `isinstance(result, DeliberationResult)`
   - Assert `result.final_response` is a non-empty string
   - Assert `result.deliberation_log` is a list of `MemberLog` instances

6. Implement `test_run_consolidated_deliberation_extracts_escalation`:
   - Stub `LLMClient.call` so council output contains one `ESCALATION: Response is out of scope` line for member "Domain Analyst"
   - Call `run_consolidated_deliberation(...)` and assert:
     - `result.escalation_triggered is True`
     - `result.escalating_member == "Domain Analyst"`
     - The evaluator call (second in `call_log`) received `escalation_summary` that contains `"out of scope"` or `"Response is out of scope"`

7. Ensure the file uses `from __future__ import annotations`, has proper type annotations on all fixtures and test functions (return type `None`), and passes `ruff check`.

## Verification

- Structural:
  - File `tests/unit/test_consolidated.py` exists
  - `grep -n 'def test_' /home/buddy/projects/corpus-council/tests/unit/test_consolidated.py` shows all 5 test functions
  - `grep -n 'mock\|Mock\|MagicMock\|patch\|render_template' /home/buddy/projects/corpus-council/tests/unit/test_consolidated.py` shows no mocking of `render_template` (monkeypatching `call` only is acceptable)
- Global constraints:
  - No mocking of template rendering: `grep -n 'render_template.*Mock\|patch.*render_template' /home/buddy/projects/corpus-council/tests/unit/test_consolidated.py` returns no matches
  - No `pytest.mark.llm` on unit tests: `grep -n 'mark.llm' /home/buddy/projects/corpus-council/tests/unit/test_consolidated.py` returns no matches
- Behavioral:
  - `uv run pytest tests/unit/test_consolidated.py -v` exits 0 with all 5 tests passing
  - `uv run ruff check tests/unit/test_consolidated.py` exits 0
  - `uv run ruff format --check tests/unit/test_consolidated.py` exits 0
- Dynamic: run the test suite and verify all 5 tests are collected and pass:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run pytest tests/unit/test_consolidated.py -v 2>&1 | tail -20
  ```
  Output must show 5 tests passed, 0 failed.

## Done When
- [ ] `tests/unit/test_consolidated.py` contains all 5 specified tests
- [ ] Template rendering tests use real `llm.render_template()` (no mocking)
- [ ] Call-count test asserts exactly 2 `llm.call()` invocations with correct template names
- [ ] Escalation extraction test drives escalation via a real parsed string (not a mock flag)
- [ ] `uv run pytest tests/unit/test_consolidated.py` exits 0 with all 5 tests passing
- [ ] All verification checks pass

## Save Command
```
git add tests/unit/test_consolidated.py && git commit -m "task-00006: write unit tests for consolidated.py"
```
