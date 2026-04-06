# Task 00004: Add mode field to API models and update routers

## Role
programmer

## Objective
Add `mode: Literal["sequential", "consolidated"] | None = None` to `ConversationRequest`, `CollectionStartRequest`, and `CollectionRespondRequest` in `src/corpus_council/api/models.py`. Update `src/corpus_council/api/routers/conversation.py` to resolve mode via `request.mode or config.deliberation_mode` and pass the resolved mode to `run_conversation()`. Update `src/corpus_council/api/routers/collection.py` similarly for `start_collection()` and `respond_collection()`. Invalid `mode` values must return HTTP 422 (enforced by Pydantic's `Literal` type).

## Context

**Task 00000** added `deliberation_mode: str` to `AppConfig`.
**Task 00003** added `mode: str = "sequential"` to `run_conversation()`, `start_collection()`, and `respond_collection()`.

**Current `src/corpus_council/api/models.py`** — relevant request models:
```python
class ConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    message: str

class CollectionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    plan_id: str

class CollectionRespondRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    session_id: str
    message: str
```

Add to each model:
```python
mode: Literal["sequential", "consolidated"] | None = None
```

The import `from typing import Literal` is already present in `models.py` (used for `CollectionRespondResponse`). Verify before adding a duplicate import.

**Current `src/corpus_council/api/routers/conversation.py`**:
```python
@router.post("/conversation", response_model=ConversationResponse)
async def post_conversation(request: ConversationRequest) -> ConversationResponse:
    from corpus_council.api.app import config, llm, store
    user_id = validate_id(request.user_id, "user_id")
    result = run_conversation(user_id, request.message, config, store, llm)
    return ConversationResponse(response=result.response, user_id=user_id)
```

Update to:
```python
    resolved_mode: str = request.mode or config.deliberation_mode
    result = run_conversation(user_id, request.message, config, store, llm, mode=resolved_mode)
```

**Current `src/corpus_council/api/routers/collection.py`**:
- `post_collection_start()` calls `start_collection(user_id, plan_id, session_id, config, store, llm)` — add `mode=resolved_mode` where `resolved_mode = request.mode or config.deliberation_mode`
- `post_collection_respond()` calls `respond_collection(user_id, session_id, request.message, config, store, llm)` — add `mode=resolved_mode`

**Mode resolution rule:** `request.mode or config.deliberation_mode`. If `request.mode` is `None`, use `config.deliberation_mode` (which defaults to `"sequential"`). This means a missing `mode` field never raises an error.

**Security constraint:** `mode` must be a Pydantic `Literal["sequential", "consolidated"]` — FastAPI/Pydantic automatically returns HTTP 422 for invalid values. Do not add manual validation beyond what Pydantic provides.

**Global constraints:**
- `mode` field in all API request bodies is `Literal["sequential", "consolidated"] | None = None` — no other type
- Invalid values must return HTTP 422, not 500
- No new Python packages
- All code must pass `mypy src/corpus_council/core/` and `ruff check src/`

## Steps

1. Open `src/corpus_council/api/models.py`. Verify `Literal` is imported (it is, from `typing`). Add `mode: Literal["sequential", "consolidated"] | None = None` to:
   - `ConversationRequest`
   - `CollectionStartRequest`
   - `CollectionRespondRequest`

2. Open `src/corpus_council/api/routers/conversation.py`. In `post_conversation()`:
   - After `user_id = validate_id(...)`, add: `resolved_mode: str = request.mode or config.deliberation_mode`
   - Replace `result = run_conversation(user_id, request.message, config, store, llm)` with `result = run_conversation(user_id, request.message, config, store, llm, mode=resolved_mode)`

3. Open `src/corpus_council/api/routers/collection.py`. In `post_collection_start()`:
   - After `plan_id = validate_id(...)`, add: `resolved_mode: str = request.mode or config.deliberation_mode`
   - Add `mode=resolved_mode` as the last argument to `start_collection(...)`

4. In `post_collection_respond()`:
   - After `session_id = validate_id(...)`, add: `resolved_mode: str = request.mode or config.deliberation_mode`
   - Add `mode=resolved_mode` as the last argument to `respond_collection(...)`

## Verification

- Structural:
  - `grep -n 'mode.*Literal.*sequential.*consolidated' /home/buddy/projects/corpus-council/src/corpus_council/api/models.py` shows matches in ConversationRequest, CollectionStartRequest, CollectionRespondRequest (3 matches)
  - `grep -n 'resolved_mode' /home/buddy/projects/corpus-council/src/corpus_council/api/routers/conversation.py` shows mode resolution
  - `grep -n 'resolved_mode' /home/buddy/projects/corpus-council/src/corpus_council/api/routers/collection.py` shows mode resolution in both handlers
- Global constraint — enum validation:
  - `grep -n "Literal\[.sequential.*consolidated" /home/buddy/projects/corpus-council/src/corpus_council/api/models.py` returns 3 matches (one per request model)
- Behavioral:
  - `uv run ruff check src/corpus_council/api/` exits 0
  - `uv run ruff format --check src/corpus_council/api/` exits 0
  - `uv run mypy src/corpus_council/core/` exits 0 (core still clean after API changes)
- Dynamic: start the app and verify 422 is returned for invalid mode:
  ```bash
  cd /home/buddy/projects/corpus-council && uv run uvicorn corpus_council.api.app:app --host 127.0.0.1 --port 18765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -s http://127.0.0.1:18765/health 2>/dev/null | grep -q 'ok\|healthy\|200\|{' && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:18765/conversation -H 'Content-Type: application/json' -d '{"user_id": "testuser", "message": "hi", "mode": "invalid_mode"}')
  kill $APP_PID
  [ "$STATUS" = "422" ] && echo "422 returned for invalid mode OK" || (echo "Expected 422, got $STATUS" && exit 1)
  ```

## Done When
- [ ] `ConversationRequest`, `CollectionStartRequest`, `CollectionRespondRequest` each have `mode: Literal["sequential", "consolidated"] | None = None`
- [ ] `post_conversation()` resolves mode via `request.mode or config.deliberation_mode` and passes to `run_conversation()`
- [ ] `post_collection_start()` and `post_collection_respond()` resolve and pass mode similarly
- [ ] Invalid `mode` value returns HTTP 422 (verified by dynamic check)
- [ ] `uv run ruff check src/corpus_council/api/` exits 0
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/api/models.py src/corpus_council/api/routers/conversation.py src/corpus_council/api/routers/collection.py && git commit -m "task-00004: add mode field to API models and update routers"
```
