# Task 00000: Update LLMClient to Support Separate System Prompt

## Role
programmer

## Objective
Update `src/corpus_council/core/llm.py` so that `LLMClient.call()` accepts an optional `system_prompt: str | None = None` parameter. When `system_prompt` is provided, it is passed as the Anthropic `system` field and the rendered template is sent as the user-turn message content. When `system_prompt` is `None`, existing behaviour is preserved (the rendered template is used as the system prompt, no user-turn message). All call sites outside `deliberation.py` are unaffected — the parameter is optional and backward-compatible.

## Context

**File:** `src/corpus_council/core/llm.py`

Read this file in full before making any change. It contains `LLMClient` which wraps `anthropic.Anthropic`. The `call()` method currently:
1. Renders a Jinja2 template from `templates/` using `render_template(template_name, context)`
2. Calls the Anthropic messages API

After this task, `call()` must support two calling conventions:

**Convention A — system_prompt not provided (current behaviour, unchanged):**
```python
llm.call("some_template", context)
# Rendered template → system prompt
# No user message
```

**Convention B — system_prompt provided (new behaviour):**
```python
llm.call("member_deliberation", context, system_prompt=rendered_system)
# rendered_system → Anthropic system field
# Rendered "member_deliberation" template → user-turn message content
```

The Anthropic messages API call structure for Convention B:
```python
client.messages.create(
    model=self.model,
    max_tokens=...,
    system=system_prompt,           # ← the pre-rendered system string
    messages=[
        {"role": "user", "content": rendered_template}  # ← template becomes user message
    ]
)
```

The Anthropic messages API call structure for Convention A (unchanged):
```python
client.messages.create(
    model=self.model,
    max_tokens=...,
    system=rendered_template,       # ← template is the system prompt
    messages=[
        {"role": "user", "content": "Please respond."}  # ← or however it currently works
    ]
)
```

Examine the existing call structure carefully — do not change Convention A's behaviour at all. Only add the branch for when `system_prompt` is provided.

**Type annotation:** `system_prompt: str | None = None` — mypy strict mode requires this to be explicit.

**`render_template` helper:** This is already on `LLMClient` (or a module-level function). It takes `(template_name: str, context: dict[str, Any]) -> str` and returns the rendered string. Use it to render the user-turn template in Convention B.

**No changes to any other file in this task.** The call sites in `deliberation.py` (which will use the new parameter) are updated in task 00003. All other callers (e.g., `consolidated.py`) continue to call `llm.call()` without `system_prompt` and are unaffected.

Tech stack: Python 3.12, `anthropic` SDK, mypy strict.

## Steps
1. Read `src/corpus_council/core/llm.py` in full.
2. Add `system_prompt: str | None = None` parameter to `LLMClient.call()`.
3. In the body of `call()`, branch on `system_prompt`:
   - If `system_prompt is not None`: render the template → user-turn content; use `system_prompt` as the Anthropic `system` field.
   - If `system_prompt is None`: preserve existing behaviour exactly.
4. Run `uv run mypy src/` and fix any type errors.
5. Run `uv run ruff check src/ && uv run ruff format --check src/` and fix any issues.
6. Run `uv run pytest tests/ -x -k "not llm"` to confirm no regressions.

## Verification
- `grep -n "system_prompt" src/corpus_council/core/llm.py` returns at least one match showing the new parameter
- `uv run mypy src/` exits 0
- `uv run ruff check src/ && uv run ruff format --check src/` exits 0
- `uv run pytest tests/ -x -k "not llm"` exits 0
- Global Constraint — No inline prompt strings: `grep -n '"""' src/corpus_council/core/llm.py` returns no multi-line prompt string literals (template rendering still goes through `render_template`)
- Global Constraint — No new Python package dependencies: `pyproject.toml` unchanged
- Dynamic: `uv run python -c "from corpus_council.core.llm import LLMClient; import inspect; sig = inspect.signature(LLMClient.call); assert 'system_prompt' in sig.parameters, 'system_prompt not in signature'; print('OK')"` exits 0 and prints "OK"

## Done When
- [ ] `LLMClient.call()` accepts `system_prompt: str | None = None`
- [ ] When `system_prompt` is provided, it is passed as Anthropic `system` field and template renders as user-turn message
- [ ] When `system_prompt` is `None`, existing behaviour is unchanged
- [ ] `uv run mypy src/` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/core/llm.py && git commit -m "task-00000: add system_prompt parameter to LLMClient.call()"
```
