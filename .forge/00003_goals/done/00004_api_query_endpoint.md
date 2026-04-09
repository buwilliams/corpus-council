# Task 00004: Update FastAPI API — POST /query endpoint with goal field

## Role
api-designer

## Objective
Update the FastAPI application to expose a `POST /query` endpoint that accepts a `goal: str` (required), `message: str`, and optional `mode`. Add `QueryRequest` and `QueryResponse` Pydantic models. Remove `POST /conversation` (or keep it only as an internal implementation detail not exposed publicly). The `collection` and `conversation` routers must not remain as publicly-dispatched endpoints if they encode the hardcoded collection/conversation distinction. All models must use `ConfigDict(extra="forbid")`. The `mode` field must be typed as `Literal["sequential", "consolidated"] | None`. The `--goal` name lookup must return HTTP 404 (not 500) when the goal is not in the manifest.

## Context
**Task 00000** added `goals_dir`, `personas_dir`, `goals_manifest_path` to `AppConfig`.
**Task 00001** implemented `load_goal(name, manifest_path) -> GoalConfig` in `goals.py`.
**Task 00003** added `load_council_for_goal` to `council.py`.

**Current API** at `/home/buddy/projects/corpus-council/src/corpus_council/api/`:
- `app.py` — creates FastAPI app, registers routers for `conversation`, `collection`, `corpus`
- `routers/conversation.py` — `POST /conversation`
- `routers/collection.py` — `POST /collection/start`, `POST /collection/respond`, `GET /collection/{user_id}/{session_id}`
- `routers/corpus.py` — `POST /corpus/ingest`, `POST /corpus/embed`
- `models.py` — `ConversationRequest`, `ConversationResponse`, `CollectionStartRequest`, etc.

**Changes needed**:
1. Add `QueryRequest` and `QueryResponse` to `models.py`:
   ```python
   class QueryRequest(BaseModel):
       model_config = ConfigDict(extra="forbid")
       message: str
       goal: str
       mode: Literal["sequential", "consolidated"] | None = None

   class QueryResponse(BaseModel):
       model_config = ConfigDict(extra="forbid")
       response: str
       goal: str
   ```
2. Create `src/corpus_council/api/routers/query.py` implementing `POST /query`:
   - Load `goal_config = load_goal(request.goal, config.goals_manifest_path)` — if `ValueError` (not found), raise `HTTPException(status_code=404, detail=f"Goal {request.goal!r} not found")`
   - Load council via `load_council_for_goal(goal_config, config.personas_dir)`
   - Retrieve corpus chunks via `retrieve_chunks(request.message, config)`
   - Resolve mode: `request.mode or config.deliberation_mode`
   - Run deliberation: `run_consolidated_deliberation` or `run_deliberation`
   - Return `QueryResponse(response=result.final_response, goal=request.goal)`
3. Register the new router in `app.py`: `app.include_router(query_router)`
4. The existing `conversation` and `collection` routers represent the old hardcoded mode distinction. Per the project spec, the collection/conversation mode distinction must be removed from core orchestration. Remove `conversation` and `collection` routers from public registration in `app.py`. The `routers/conversation.py` and `routers/collection.py` files may be deleted or left in place but must not be included in `app.py`'s router registration. The `corpus` router stays.
5. Update exception handlers in `app.py` to ensure `ValueError` from `load_goal` surfaces as 404:
   - Add an `HTTPException` import and an explicit handler or use `raise HTTPException(status_code=404, ...)` inside the endpoint itself (preferred, since `ValueError` could mean other things).
6. The `test_api.py` integration test currently tests `POST /conversation` and `POST /collection/*` endpoints. These tests will break when those routes are removed. The agent must update `test_api.py` to test `POST /query` instead. Updated tests:
   - `test_post_query_returns_200` — POST `/query` with valid `goal` (use a goal written to `tmp_path/goals/` and loaded via a patched config), valid `message` → expect 200, `response` and `goal` in body
   - `test_post_query_unknown_goal_returns_404` — POST `/query` with `goal="nonexistent"` → expect 404 with `error` or `detail` in body
   - `test_post_query_mode_invalid_returns_422` — POST `/query` with `mode="invalid"` → expect 422
   - `test_post_query_mode_consolidated_returns_200` — POST `/query` with `mode="consolidated"` → expect 200
   - `test_post_corpus_ingest_returns_200` and `test_post_corpus_embed_returns_200` — retain as-is (corpus router unchanged)
   The `TestLLM` fixture in `test_api.py` (which stubs HTTP transport but exercises real template rendering) must also be updated: the `council_consolidated` and `member_deliberation` template stubs may need to be present. Keep `render_template` calls real; only stub the Anthropic HTTP call.

**Important**: The `conftest.py` `test_config` fixture needs a `goals_dir` pointing to a tmp directory with at least one valid goal file (populated with fake persona references that the fixture also creates in its `council_dir`). This wiring is needed so `POST /query` can actually find a goal. Add a `goals_dir` fixture to `conftest.py` that creates a goal file referencing the council members from `council_dir`. The goal file's `persona_file` values must match the persona filenames in `council_dir` (from `conftest.py` those are `synthesizer.md`, `analyst.md`, `critic.md`). Also add `goals_manifest_path` fixture pointing to `tmp_path / "goals_manifest.json"`.

**mypy strict**: All new files must use `from __future__ import annotations`. All function signatures fully typed. No `Any` except where unavoidable (with documented `# type: ignore`).

## Steps
1. Add `QueryRequest` and `QueryResponse` to `src/corpus_council/api/models.py`.
2. Create `src/corpus_council/api/routers/query.py` with the `POST /query` endpoint (see Context above).
3. Update `src/corpus_council/api/app.py`:
   a. Import and register `query_router` from `routers/query.py`
   b. Remove `conversation.router` and `collection.router` from `app.include_router` calls
   c. Keep `corpus.router`
4. Update `tests/conftest.py`:
   a. Add a `goals_dir` fixture that creates `tmp_path/goals/` and writes a goal file `test-goal.md` referencing `synthesizer.md` and `analyst.md` (matching the existing `council_dir` fixture)
   b. Update the `test_config` fixture to pass `goals_dir=goals_dir` and `goals_manifest_path=tmp_path / "goals_manifest.json"` to `AppConfig`
   c. Optionally call `process_goals(goals_dir, council_dir, tmp_path / "goals_manifest.json")` in the fixture so the manifest is pre-generated for API tests — but only if this doesn't break unit tests that expect an empty manifest
5. Update `tests/integration/test_api.py` to replace old `conversation`/`collection` endpoint tests with the new `POST /query` tests (see Context above). Keep corpus endpoint tests.
6. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest` and fix any issues.

## Verification
- Structural: `src/corpus_council/api/routers/query.py` exists and defines a `POST /query` endpoint
- Structural: `src/corpus_council/api/models.py` contains `QueryRequest` and `QueryResponse` with `goal: str` field
- Structural: `src/corpus_council/api/app.py` registers the query router and does NOT register conversation or collection routers
- Structural: Grep `src/corpus_council/api/app.py` for `conversation.router` and `collection.router` — must not appear as `include_router` calls
- Structural: Grep `src/corpus_council/api/routers/query.py` for `"collection"` or `"conversation"` dispatch strings — must be absent
- Behavioral: `uv run mypy src/` exits 0
- Behavioral: `uv run ruff check .` exits 0
- Behavioral: `uv run ruff format --check .` exits 0
- Behavioral: `uv run pytest` exits 0
- Constraint (mode field is Literal, not str): Grep `src/corpus_council/api/models.py` for `Literal["sequential", "consolidated"]` in `QueryRequest` — must be present
- Constraint (no hardcoded collection/conversation dispatch): Grep `src/corpus_council/api/` for routing on literal strings `"collection"` or `"conversation"` — must return no matches in public routing logic
- Constraint (no new external packages): `pyproject.toml` dependencies unchanged
- Dynamic: Start a test server and exercise `POST /query`:
  ```bash
  uv run pytest tests/integration/test_api.py -v 2>&1 | tail -20
  ```
  All `test_post_query_*` tests must pass.

## Done When
- [ ] `POST /query` endpoint exists and accepts `goal`, `message`, and optional `mode`
- [ ] Unknown `goal` returns HTTP 404
- [ ] Invalid `mode` returns HTTP 422
- [ ] Old `conversation` and `collection` routers removed from public API
- [ ] `test_api.py` updated and `uv run pytest` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/api/ tests/conftest.py tests/integration/test_api.py && git commit -m "task-00004: add POST /query endpoint with goal field, remove conversation/collection routers"
```
