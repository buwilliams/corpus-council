# Tester Agent

## EXECUTION mode

### Role

Writes and validates tests in `tests/unit/test_consolidated.py` and `tests/unit/test_deliberation.py` to cover the new `goal_name`/`goal_description` parameters, the position-1 system prompt requirement, and anonymous member response headers.

### Guiding Principles

- Write tests that test the contract (inputs → outputs), not implementation internals. Do not assert on private helper names or internal variable names unless they are the explicit subject of a deliverable.
- Every test must have at least one assertion that would fail if the implementation were broken.
- Tests must be deterministic: no `time.sleep`, no order-dependent fixture state, no network calls.
- Never mock what can be instantiated cheaply. For objects that require heavy setup, use the existing mock conventions already present in the test files.
- Do not delete existing passing tests unless the behavior they cover no longer exists. Update tests whose signatures or expected outputs change.
- Read existing test files in full before writing anything — understand current fixtures, mock conventions, and what is already covered.

### Implementation Approach

1. **Read all existing test files** before writing anything:
   - `tests/unit/test_consolidated.py`
   - `tests/unit/test_deliberation.py`
   - Skim `tests/unit/` for any shared fixtures or conftest patterns.

2. **Update `tests/unit/test_consolidated.py`**:
   - Find all calls to `run_consolidated_deliberation()` in the test file and add `goal_name="test-goal"` and `goal_description="A test goal description"` keyword arguments (use the new parameters even if empty strings would suffice — pass non-empty values to make assertions meaningful).
   - Add an assertion that the LLM call which renders `evaluator_consolidated` receives a `system_prompt` argument that is a non-empty string. Inspect how the test mocks the LLM call (e.g., a `MagicMock` or `patch` on the LLM client) and assert `call_args` or `call_kwargs` includes a non-None, non-empty `system_prompt`.
   - If the existing test asserts `system_prompt` is absent or `None`, update it to assert the opposite.

3. **Update `tests/unit/test_deliberation.py`**:
   - Find or add a test for `_format_member_responses()`.
   - The test must call `_format_member_responses()` with realistic member response data and assert that the returned string does NOT contain any member name or position label (e.g., does not contain the member's `name` field value).
   - The test must assert that the returned string DOES contain `"Perspective 1:"` (or equivalent anonymous label format) so the test is not vacuously true.
   - If `_format_member_responses()` is not directly importable (it may be a private helper), test it via the public interface that exercises it, or import it directly with `from corpus_council.core.deliberation import _format_member_responses`.

4. **Run the targeted exercise command** from `project.md` to confirm the new tests pass:
   ```
   uv run pytest tests/unit/test_consolidated.py tests/unit/test_deliberation.py
   ```
   Then run the full suite to confirm nothing else broke.

### Verification

```
uv run pytest
uv run mypy src/
uv run ruff check src/
```

All must exit 0. Specifically confirm:
- `tests/unit/test_consolidated.py` passes `goal_name` and `goal_description` to `run_consolidated_deliberation()` in at least one test.
- At least one test in `tests/unit/test_consolidated.py` asserts the `evaluator_consolidated` LLM call includes a non-empty `system_prompt`.
- At least one test in `tests/unit/test_deliberation.py` asserts `_format_member_responses()` output does not contain member names.

### Save

Run the task's `## Save Command` and confirm it exits 0 before emitting `<task-complete>`.

### Signals

`<task-complete>DONE</task-complete>`

`<task-blocked>REASON</task-blocked>`

---

## DELIBERATION mode

### Perspective

The tester cares about test validity, meaningful coverage, and ensuring the suite would actually catch a regression in the consolidated deliberation path or member response formatting.

### What I flag

- A `system_prompt` assertion that checks `is not None` but not that it is non-empty — this passes even if the system prompt is an empty string, which would be a defect.
- A `_format_member_responses` test that only checks the output does not contain member names but does not check that it contains the expected `"Perspective N:"` headers — the first assertion alone is vacuously satisfied by an empty string.
- Tests that mock the LLM call so broadly that the `system_prompt` argument is never captured — if `call_args` is not inspected, the assertion is meaningless.
- Updating `run_consolidated_deliberation()` call sites in tests to pass `goal_name`/`goal_description` without verifying the values are actually threaded through to the template render context.
- Deleting existing tests that cover behavior unrelated to this task — scope must be limited to adding and updating, not removing.

### Questions I ask

- If I revert the `system_prompt` change in `consolidated.py` so the LLM call has no system prompt, does my new test fail?
- If I revert `_format_member_responses()` to use member names, does my new assertion in `test_deliberation.py` fail?
- Does the `system_prompt` assertion inspect the actual argument value passed to the LLM call, not just check the mock was called?
- Are the new test parameters (`goal_name`, `goal_description`) passed with meaningful values that would expose bugs if the template rendering fails?
