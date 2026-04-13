# Task 00003: Update Tests

## Role
tester

## Objective
Update `tests/unit/test_consolidated.py` and `tests/unit/test_deliberation.py` to cover the new `run_consolidated_deliberation()` signature (with `goal_name`/`goal_description`), assert that the evaluator LLM call receives a non-empty `system_prompt`, and assert that `_format_member_responses()` output does not contain member names.

## Context

**Files to modify:**
- `/home/buddy/projects/corpus-council/tests/unit/test_consolidated.py`
- `/home/buddy/projects/corpus-council/tests/unit/test_deliberation.py`

**Do not delete any existing passing tests** unless the behavior they cover has been entirely removed. Update tests whose signatures or expected outputs change.

**Current state of `test_consolidated.py`:**

There are 4 tests:
1. `test_council_consolidated_template_renders_all_personas` — real render, no mock; unchanged.
2. `test_evaluator_consolidated_template_renders_inputs` — real render, no mock. After Task 00001, the template renames `## Council Responses` to `## Internal Analysis` and removes the evaluator preamble. This test currently asserts `user_message in rendered` and `"Domain Analyst" in rendered`. The second assertion (`"Domain Analyst" in rendered`) passes because the `council_output` stub passed as `council_responses` contains "Domain Analyst" — this is the raw consolidated output block, not a section label. So this test should still pass after Task 00001. No change needed unless it fails.
3. `test_run_consolidated_deliberation_makes_exactly_two_calls` — uses `monkeypatch`. The `fake_call` signature is `(self, template_name, context)` with no `system_prompt` argument. After Task 00002, `llm.call("evaluator_consolidated", ...)` will be called with `system_prompt=position_one_system_prompt`. The fake needs to accept `**kwargs` or add `system_prompt: str | None = None` — otherwise the call will either fail or the assertion will miss the argument. This test must be updated.
4. `test_run_consolidated_deliberation_returns_deliberation_result` — same issue with `fake_call` signature.
5. `test_run_consolidated_deliberation_extracts_escalation` — same issue; additionally captures `evaluator_contexts` from the `context` arg. The `system_prompt` is a separate keyword arg, not in `context`.

**Changes needed in `test_consolidated.py`:**

A. **Update all `fake_call` stubs** to accept `system_prompt: str | None = None` as a keyword argument. Current signature: `def fake_call(self: LLMClient, template_name: str, context: dict[str, Any]) -> str`. New signature: `def fake_call(self: LLMClient, template_name: str, context: dict[str, Any], system_prompt: str | None = None) -> str`.

B. **Add `goal_name` and `goal_description`** keyword arguments to all `run_consolidated_deliberation()` calls in the test file. Use `goal_name="test-goal"` and `goal_description="A test goal description"` (non-empty values to make assertions meaningful).

C. **Add a new test** (or extend an existing one) that asserts the evaluator LLM call passes a non-empty `system_prompt`. The approach: capture `system_prompt` values by template name in a `fake_call` stub, then assert that the call for `"evaluator_consolidated"` received a non-None, non-empty string for `system_prompt`. Name the test `test_run_consolidated_deliberation_evaluator_receives_system_prompt`.

**Note on `test_evaluator_consolidated_template_renders_inputs`:** This test uses `council_responses` as the context key (matching the current template variable name, which is unchanged after Task 00001 — only the section header changes, not the Jinja2 variable). This test should continue to pass without modification. If Task 00001 changed the variable name (it should not have), update accordingly.

**Current state of `test_deliberation.py`:**

The file imports `_format_member_responses` (along with other symbols) from `corpus_council.core.deliberation` — wait, actually looking at the current import block:
```python
from corpus_council.core.deliberation import (
    DeliberationResult,
    MemberLog,
    _format_chunks,
    run_deliberation,
)
```
`_format_member_responses` is NOT currently imported. It needs to be added to the import.

**Changes needed in `test_deliberation.py`:**

A. **Add `_format_member_responses` to the import** from `corpus_council.core.deliberation`.

B. **Add a new test** `test_format_member_responses_uses_anonymous_headers` that:
   - Constructs a small `list[MemberLog]` with at least 2 members, using known `member_name` values (e.g., "Final Synthesizer" and "Domain Analyst").
   - Calls `_format_member_responses(log)`.
   - Asserts the returned string does NOT contain `"Final Synthesizer"` or `"Domain Analyst"` (or any member name).
   - Asserts the returned string DOES contain `"Perspective 1:"` (verifying the anonymous header format, not just absence of names).
   - Asserts the returned string DOES contain the actual response content from each `MemberLog.response` field (verifying content is not lost).

C. **Existing `test_member_responses_in_synthesis_context`** — this test asserts `"member_responses" in synthesis_calls[0]["context"]`. After Task 00002, the `member_responses` value in that context will use `Perspective N:` headers instead of member names, but the key `"member_responses"` is still present. This test still passes; no change needed.

## Steps

1. **Read both test files** in full before editing:
   - `/home/buddy/projects/corpus-council/tests/unit/test_consolidated.py`
   - `/home/buddy/projects/corpus-council/tests/unit/test_deliberation.py`

2. **Update `tests/unit/test_consolidated.py`**:

   a. Add `system_prompt: str | None = None` parameter to every `fake_call` definition in the file (there are 3 `fake_call` functions across 3 tests).

   b. Add `goal_name="test-goal"` and `goal_description="A test goal description"` to every `run_consolidated_deliberation()` call that uses the mock (tests 3, 4, and 5 in the file).

   c. Add a new test:
   ```python
   def test_run_consolidated_deliberation_evaluator_receives_system_prompt(
       monkeypatch: pytest.MonkeyPatch,
   ) -> None:
       """Evaluator LLM call must receive a non-empty system_prompt from position-1's persona."""
       config = _make_config()
       llm = LLMClient(config)
       members = _make_members()

       council_output = _make_normal_council_output(members)
       captured_system_prompts: dict[str, str | None] = {}

       def fake_call(
           self: LLMClient,
           template_name: str,
           context: dict[str, Any],
           system_prompt: str | None = None,
       ) -> str:
           captured_system_prompts[template_name] = system_prompt
           if template_name == "council_consolidated":
               return council_output
           return "Final synthesized answer."

       monkeypatch.setattr(LLMClient, "call", fake_call)

       run_consolidated_deliberation(
           user_message="What is AI?",
           corpus_chunks=[],
           members=members,
           llm=llm,
           goal_name="test-goal",
           goal_description="A test goal description",
       )

       evaluator_sp = captured_system_prompts.get("evaluator_consolidated")
       assert evaluator_sp is not None, "evaluator_consolidated LLM call must receive a system_prompt"
       assert evaluator_sp != "", "system_prompt must be non-empty"
   ```

3. **Update `tests/unit/test_deliberation.py`**:

   a. Add `_format_member_responses` to the import block:
   ```python
   from corpus_council.core.deliberation import (
       DeliberationResult,
       MemberLog,
       _format_chunks,
       _format_member_responses,
       run_deliberation,
   )
   ```

   b. Add the new test (place it in a new `# _format_member_responses` section after the `_format_chunks` tests):
   ```python
   # ---------------------------------------------------------------------------
   # _format_member_responses
   # ---------------------------------------------------------------------------


   def test_format_member_responses_uses_anonymous_headers() -> None:
       log = [
           MemberLog(
               member_name="Final Synthesizer",
               position=1,
               response="Response from synthesizer.",
               escalation_triggered=False,
           ),
           MemberLog(
               member_name="Domain Analyst",
               position=2,
               response="Response from analyst.",
               escalation_triggered=False,
           ),
       ]
       result = _format_member_responses(log)

       # Must not contain any member names
       assert "Final Synthesizer" not in result
       assert "Domain Analyst" not in result

       # Must contain anonymous Perspective headers
       assert "Perspective 1:" in result
       assert "Perspective 2:" in result

       # Must preserve response content
       assert "Response from synthesizer." in result
       assert "Response from analyst." in result
   ```

4. **Run the targeted exercise command** from `project.md`:
   ```
   uv run pytest tests/unit/test_consolidated.py tests/unit/test_deliberation.py
   ```
   Both files must pass. Then run the full suite:
   ```
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```

## Verification

- `uv run pytest tests/unit/test_consolidated.py tests/unit/test_deliberation.py` exits 0.
- `uv run pytest` exits 0 (full suite).
- `uv run mypy src/` exits 0.
- `uv run ruff check src/` exits 0.
- At least one test in `test_consolidated.py` passes `goal_name` and `goal_description` to `run_consolidated_deliberation()`.
- At least one test in `test_consolidated.py` asserts `evaluator_consolidated` LLM call received a non-None, non-empty `system_prompt`.
- At least one test in `test_deliberation.py` asserts `_format_member_responses()` output does not contain member names.
- At least one test in `test_deliberation.py` asserts `_format_member_responses()` output contains `"Perspective 1:"`.
- No existing passing tests deleted.

## Done When
- [ ] All `fake_call` stubs in `test_consolidated.py` accept `system_prompt: str | None = None`.
- [ ] All `run_consolidated_deliberation()` calls in `test_consolidated.py` pass `goal_name="test-goal"` and `goal_description="A test goal description"`.
- [ ] `test_run_consolidated_deliberation_evaluator_receives_system_prompt` added and asserts non-empty `system_prompt` on evaluator call.
- [ ] `_format_member_responses` imported in `test_deliberation.py`.
- [ ] `test_format_member_responses_uses_anonymous_headers` added and asserts: no member names present, `Perspective 1:` present, response content preserved.
- [ ] `uv run pytest tests/unit/test_consolidated.py tests/unit/test_deliberation.py` exits 0.
- [ ] `uv run pytest` exits 0.
- [ ] `uv run mypy src/` exits 0.
- [ ] `uv run ruff check src/` exits 0.

## Save Command
```
git add tests/unit/test_consolidated.py tests/unit/test_deliberation.py && git commit -m "task-00003: update tests — consolidated goal params, system prompt assertion, anonymous member headers"
```
