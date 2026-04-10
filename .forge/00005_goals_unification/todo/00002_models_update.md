# Task 00002: Update models.py — add ChatRequest/ChatResponse, remove obsolete models

## Role
programmer

## Objective
Modify `src/corpus_council/api/models.py` to add `ChatRequest` and `ChatResponse` Pydantic models and remove all obsolete models that belong to the deleted query/conversation/collection surfaces: `ConversationRequest`, `ConversationResponse`, `CollectionStartRequest`, `CollectionStartResponse`, `CollectionRespondRequest`, `CollectionRespondResponse`, `CollectionStatusResponse`, `QueryRequest`, `QueryResponse`.

## Context

**File to modify:** `src/corpus_council/api/models.py`

**Current state of models.py:** Contains the following classes that must be REMOVED:
- `ConversationRequest`
- `ConversationResponse`
- `CollectionStartRequest`
- `CollectionStartResponse`
- `CollectionRespondRequest`
- `CollectionRespondResponse`
- `CollectionStatusResponse`
- `QueryRequest`
- `QueryResponse`

**Models to KEEP** (these are used by admin, corpus, and files routers):
- `ErrorResponse`
- `CorpusIngestRequest`
- `CorpusIngestResponse`
- `CorpusEmbedResponse`
- `FileEntry`
- `DirectoryListingResponse`
- `FileContentResponse`
- `FileRootsResponse`
- `FileWriteRequest`
- `ConfigResponse`
- `ConfigWriteRequest`
- `GoalsProcessResponse`
- `GoalSummary`
- `GoalsListResponse`

**New models to ADD:**
```python
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    user_id: str
    conversation_id: str | None = None
    message: str
    mode: str | None = None

class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    goal: str
    conversation_id: str
```

**Important:** `QueryRequest` used `Literal["sequential", "consolidated"] | None` for `mode`. The new `ChatRequest` uses plain `str | None` for `mode` — this is intentional (mode validation happens in the core layer).

**Context on obsolete router files:** The old routers (`query.py`, `conversation.py`, `collection.py`) import the obsolete models. Those routers will be deleted in Task 00003. At this point the old router files still exist on disk but will fail to import after the models are removed. The `app.py` still imports and registers those routers — this will cause import errors until Task 00003 updates `app.py`. **Therefore, Task 00002 and Task 00003 must be verified together.** The verification for this task uses the state after Task 00003 is applied (i.e., after `app.py` is updated and old routers are deleted). However, the unit-level verification (pyright, ruff on `models.py` alone) can be checked immediately.

**For this task's verification:** Run pyright and ruff checks after the models update. Do NOT try to start the uvicorn server at this point because `app.py` still imports the old routers. The dynamic check will be added in Task 00003.

**Tech stack:** Python 3.12, Pydantic v2, uv.

## Steps
1. Open `src/corpus_council/api/models.py`.
2. Remove the nine obsolete model classes: `ConversationRequest`, `ConversationResponse`, `CollectionStartRequest`, `CollectionStartResponse`, `CollectionRespondRequest`, `CollectionRespondResponse`, `CollectionStatusResponse`, `QueryRequest`, `QueryResponse`.
3. Remove the `Literal` import if it is only used by the removed models. Keep `Any` only if used by remaining models (it is used by `CollectionRespondResponse.collected` — which is being removed, so remove `Any` only if no remaining model uses it). Check: `FileRootsResponse` does not use `Any`. The only `Any` usage was in the collection models — so remove `Any` from the import if all `Any`-using models are gone.
4. Add `ChatRequest` and `ChatResponse` classes after `ErrorResponse` (or at a logical location near the top of the domain models).
5. Verify `ConfigDict` is imported from `pydantic` (it already is).
6. Run `uv run ruff check src/corpus_council/api/models.py && uv run ruff format --check src/corpus_council/api/models.py` and fix any issues.
7. Run `uv run pyright src/corpus_council/api/models.py` and confirm exit 0.

## Verification
- `src/corpus_council/api/models.py` defines `ChatRequest` with fields: `goal`, `user_id`, `conversation_id`, `message`, `mode`
- `src/corpus_council/api/models.py` defines `ChatResponse` with fields: `response`, `goal`, `conversation_id`
- `src/corpus_council/api/models.py` contains no reference to `ConversationRequest`
- `src/corpus_council/api/models.py` contains no reference to `ConversationResponse`
- `src/corpus_council/api/models.py` contains no reference to `CollectionStartRequest`
- `src/corpus_council/api/models.py` contains no reference to `CollectionStartResponse`
- `src/corpus_council/api/models.py` contains no reference to `CollectionRespondRequest`
- `src/corpus_council/api/models.py` contains no reference to `CollectionRespondResponse`
- `src/corpus_council/api/models.py` contains no reference to `CollectionStatusResponse`
- `src/corpus_council/api/models.py` contains no reference to `QueryRequest`
- `src/corpus_council/api/models.py` contains no reference to `QueryResponse`
- `uv run ruff check src/corpus_council/api/models.py && uv run ruff format --check src/corpus_council/api/models.py` exits 0
- `pyproject.toml` is unchanged
- Dynamic: (deferred to Task 00003 — the server cannot start until app.py is updated and old routers are deleted)

## Done When
- [ ] `ChatRequest` and `ChatResponse` defined in `models.py`
- [ ] All nine obsolete models removed from `models.py`
- [ ] ruff and pyright pass on `models.py`
- [ ] All verification checks pass

## Save Command
```
git add src/corpus_council/api/models.py && git commit -m "task-00002: update models.py — add ChatRequest/ChatResponse, remove obsolete models"
```
