# Task 00006: Update README.md Deliberation Modes Documentation

## Role
product-manager

## Objective
Update `README.md` to replace all references to `"sequential"` mode with `"parallel"` mode. The deliberation modes table must show `parallel` as the default with accurate LLM call counts (N+1 for N non-position-1 members). All example snippets, config examples, API examples, and help text that mention `sequential` must be updated. No new sections are added — this is a targeted update only.

## Context

**File: `README.md`** (project root)

Current content includes these sections that reference `"sequential"`:

**Deliberation Modes table** (currently):
```markdown
| Mode | LLM calls | Description |
|------|-----------|-------------|
| `sequential` (default) | 2N+1 (N = council size) | Each member deliberates in turn; a final synthesizer resolves the result. Slower but each member sees prior context. |
| `consolidated` | 2 | All members respond in a single call, then an evaluator synthesizes the final answer. Faster — sub-30s for a 6-member council. |
```

Update to:
```markdown
| Mode | LLM calls | Description |
|------|-----------|-------------|
| `parallel` (default) | N+1 (N = non-position-1 members) | Each member deliberates independently with no visibility into other members' responses; the position-1 member synthesizes all responses. Concurrent — wall-clock time ~2 serial LLM round-trips. |
| `consolidated` | 2 | All members respond in a single call, then an evaluator synthesizes the final answer. Faster — sub-30s for a 6-member council. |
```

**"How It Works" section** — currently step 6 says:
```
6. In **sequential** mode each member responds in turn, seeing the chunks and all prior members' responses; the position-1 member synthesizes the final answer.
```
Update to:
```
6. In **parallel** mode all non-position-1 members respond concurrently with no visibility into each other's responses; the position-1 member synthesizes all independent responses into the final answer.
```

**config.yaml example** in README — currently shows:
```yaml
deliberation_mode: sequential  # or: consolidated
```
Update to:
```yaml
deliberation_mode: parallel  # or: consolidated
```

**"Priority order" note** — currently ends with `→ sequential default`. Update to `→ parallel default`.

**API example** — currently:
```json
{ "message": "Your question", "goal": "intake", "mode": "sequential" }
```
Update to:
```json
{ "message": "Your question", "goal": "intake", "mode": "parallel" }
```

**API endpoint docs** — `mode` description currently `"sequential" or "consolidated"`. Update to `"parallel" or "consolidated"`.

Do not change: Setup section, Goals section, Workflow section (except deliberation_mode example), API Endpoints table structure, security/auth sections, or any unrelated content.

Tech stack: Markdown. No code changes.

## Steps
1. Read `README.md` in full.
2. Update the Deliberation Modes table row for the default mode.
3. Update the "How It Works" step 6 description.
4. Update the `deliberation_mode: sequential` config example.
5. Update the "Priority order" line.
6. Update the API example JSON body.
7. Update the `mode` field description in the API docs.
8. Search for any remaining `sequential` in the file and update or remove each occurrence.
9. Write the updated file.

## Verification
- `grep -n "sequential" README.md` returns no matches
- `grep -n "parallel" README.md` shows at least 4 occurrences (table, How It Works, config example, API example)
- `grep -n "deliberation_mode: parallel" README.md` returns a match
- Global Constraint — `"sequential"` absent from user-facing content: `grep -r "sequential" README.md` returns no matches
- Dynamic: `grep -c "sequential" README.md` returns `0` (exits 0 only if the pattern is absent and count is 0; use `[ $(grep -c "sequential" README.md) -eq 0 ]` to assert)

## Done When
- [ ] `README.md` contains no occurrences of `"sequential"`
- [ ] The deliberation modes table shows `parallel` as the default with correct LLM call count (N+1)
- [ ] Config example, API example, and priority note all say `parallel`

## Save Command
```
git add README.md && git commit -m "task-00005: update README to replace sequential with parallel mode"
```
