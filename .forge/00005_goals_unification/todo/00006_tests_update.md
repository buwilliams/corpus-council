# Task 00006: Update tests — integration tests for POST /chat, remove old endpoint tests

## Role
tester

## Objective
Add integration tests for `POST /chat` in `tests/integration/test_chat_router.py`. Add unit tests for `run_goal_chat` in `tests/unit/test_chat.py` (if not already created by Task 00001 — check first). Remove obsolete integration test files that test deleted endpoints. Update `tests/integration/test_router_registration.py` to reflect the new route set. Remove the `test_goals_integration.py` tests that reference the deleted `query` CLI command.

## Context

**Dependencies:**
- Task 00001 created `src/corpus_council/core/chat.py` and may have created `tests/unit/test_chat.py`
- Task 00003 created `src/corpus_council/api/routers/chat.py` and deleted old routers

**Files to CREATE:**
- `tests/integration/test_chat_router.py`

**Files to DELETE:**
- `tests/integration/test_api.py` (tests `POST /query` — obsolete)
- `tests/integration/test_full_conversation_flow.py` (tests `run_conversation` — obsolete)
- `tests/integration/test_full_collection_flow.py` (tests collection — obsolete)

**Files to MODIFY:**
- `tests/integration/test_router_registration.py` — remove assertions for `/conversation`, `/collection/start`, `/collection/respond`; add assertion for `/chat`
- `tests/integration/test_goals_integration.py` — remove `test_query_with_goal_intake`, `test_query_with_goal_create_plan`, `test_query_with_unknown_goal_exits_nonzero` (they test the deleted `query` CLI command); keep `test_goals_process_command_exits_zero`
- `tests/unit/test_chat.py` — if Task 00001 already created this file, verify it covers all required cases; if not, create it here

---

### test_chat_router.py integration tests

**Pattern to follow:** `tests/integration/test_api.py` (the file being deleted). Use `httpx.AsyncClient + ASGITransport`. Do NOT mock `FileStore`, goal manifest loading, or corpus retrieval — these must run real.

The `TestLLM` pattern (subclass of `LLMClient` with a `call` override that still calls `self.render_template()`) must be used to avoid real Anthropic API calls.

**Fixture:**
```python
@pytest.fixture
async def client(
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", ChatTestLLM(test_config))

    from corpus_council.api.app import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

**`ChatTestLLM` pattern:**
```python
class ChatTestLLM(LLMClient):
    __test__ = False

    def call(self, template_name: str, context: dict) -> str:
        self.render_template(template_name, context)  # real rendering (validates template)
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        if template_name == "council_consolidated":
            return (
                "=== MEMBER: Test Member ===\n"
                "This is a test response.\n"
                "ESCALATION: NONE\n"
                "=== END MEMBER ==="
            )
        return "Mock chat response"
```

**Required test cases:**

1. `test_post_chat_first_message_auto_generates_conversation_id`:
   - POST `/chat` with `{"goal": "test-goal", "user_id": "user0001", "message": "hello"}`
   - Assert status 200
   - Assert response body has `response`, `goal`, `conversation_id`
   - Assert `conversation_id` is a non-empty string (UUID format)
   - Assert `goal == "test-goal"`

2. `test_post_chat_continuation_uses_same_conversation_id`:
   - First POST with no `conversation_id` — capture `conv_id` from response
   - Second POST with `conversation_id=conv_id`
   - Assert second response status 200 and `conversation_id == conv_id`
   - Assert the messages file has 2 records (verify via `FileStore.goal_messages_path`)

3. `test_post_chat_unknown_goal_returns_404`:
   - POST `/chat` with `{"goal": "nonexistent-goal", "user_id": "user0001", "message": "hello"}`
   - Assert status 404

4. `test_post_chat_invalid_user_id_returns_422`:
   - POST `/chat` with `{"goal": "test-goal", "user_id": "x", "message": "hello"}` (too short — validate_id requires >=4 chars)
   - Assert status 422

5. `test_post_chat_rejects_extra_fields`:
   - POST `/chat` with extra field `"foo": "bar"`
   - Assert status 422

6. `test_post_chat_invalid_conversation_id_returns_400`:
   - POST `/chat` with `conversation_id="../../../etc"` (contains `..`)
   - Assert status 400

**Note on FileStore in test 2:** Use the `file_store` fixture from `conftest.py` to verify persistence. Add `file_store: FileStore` as a fixture parameter if needed, or pass via monkeypatch.

---

### test_router_registration.py changes

Remove these tests (they assert old routes exist):
- `test_conversation_router_registered`
- `test_collection_start_router_registered`
- `test_collection_respond_router_registered`

Add this test:
```python
async def test_chat_router_registered(client: httpx.AsyncClient) -> None:
    """POST /chat is present in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/chat" in paths, f"Expected /chat in paths, got: {list(paths.keys())}"
    assert "post" in paths["/chat"]
```

Keep: `test_files_router_registered`, `test_admin_config_router_registered`, `test_admin_goals_process_router_registered`.

---

### test_goals_integration.py changes

Remove these test functions (they reference the deleted `query` CLI command):
- `test_query_with_goal_intake`
- `test_query_with_goal_create_plan`
- `test_query_with_unknown_goal_exits_nonzero`

Keep: `test_goals_process_command_exits_zero`

---

### core/conversation.py and core/collection.py deletion

Before deleting, verify no remaining callers exist in `src/`. After Tasks 00003 and 00004, no `src/` file imports from `core/conversation.py` or `core/collection.py`. Delete both files.

**Check for callers first:**
```bash
grep -r "from.*conversation import\|import.*conversation" src/corpus_council/ | grep -v ".pyc"
grep -r "from.*collection import\|import.*collection" src/corpus_council/ | grep -v ".pyc"
```
If no output (or only from files being deleted), proceed with deletion.

**Files to delete:**
- `src/corpus_council/core/conversation.py`
- `src/corpus_council/core/collection.py`

---

### Tech stack

Python 3.12, pytest, httpx, ASGITransport, asyncio_mode = "auto" (already set in `pyproject.toml`).

## Steps
1. Check if `tests/unit/test_chat.py` already exists (from Task 00001). If it covers all required cases (first-call, continuation, unknown goal raises KeyError), keep it. If missing cases, add them.
2. Create `tests/integration/test_chat_router.py` with the 6 integration tests described above.
3. Modify `tests/integration/test_router_registration.py`:
   - Remove `test_conversation_router_registered`, `test_collection_start_router_registered`, `test_collection_respond_router_registered`
   - Add `test_chat_router_registered`
4. Modify `tests/integration/test_goals_integration.py`:
   - Remove `test_query_with_goal_intake`, `test_query_with_goal_create_plan`, `test_query_with_unknown_goal_exits_nonzero`
5. Delete `tests/integration/test_api.py`, `tests/integration/test_full_conversation_flow.py`, `tests/integration/test_full_collection_flow.py`.
6. Verify no remaining callers of `core/conversation.py` or `core/collection.py` in `src/`.
7. Delete `src/corpus_council/core/conversation.py` and `src/corpus_council/core/collection.py`.
8. Run `uv run pytest` and confirm all tests pass.
9. Run `uv run pyright src/` and confirm exit 0.
10. Run `uv run ruff check . && uv run ruff format --check .` and confirm exit 0.

## Verification
- File `tests/integration/test_chat_router.py` exists
- `tests/integration/test_chat_router.py` defines `test_post_chat_first_message_auto_generates_conversation_id`
- `tests/integration/test_chat_router.py` defines `test_post_chat_continuation_uses_same_conversation_id`
- `tests/integration/test_chat_router.py` defines `test_post_chat_unknown_goal_returns_404`
- `tests/integration/test_chat_router.py` defines `test_post_chat_invalid_user_id_returns_422`
- File `tests/integration/test_api.py` does NOT exist
- File `tests/integration/test_full_conversation_flow.py` does NOT exist
- File `tests/integration/test_full_collection_flow.py` does NOT exist
- File `src/corpus_council/core/conversation.py` does NOT exist
- File `src/corpus_council/core/collection.py` does NOT exist
- `tests/integration/test_router_registration.py` contains no reference to `test_conversation_router_registered`
- `tests/integration/test_router_registration.py` contains `test_chat_router_registered`
- `uv run pytest` exits 0
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged
- No test files in `tests/` use `MagicMock` or `unittest.mock` on `FileStore`, goal manifest loading, or corpus retrieval (integration tests only)
- Dynamic: start, POST /chat with test-goal user, verify JSON response shape, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  uv run pytest tests/integration/test_chat_router.py -x -q 2>&1 | tail -5
  STATUS=${PIPESTATUS[0]}
  kill $APP_PID
  exit $STATUS
  ```

## Done When
- [ ] `tests/integration/test_chat_router.py` created with 6 tests
- [ ] Old integration test files deleted
- [ ] `core/conversation.py` and `core/collection.py` deleted
- [ ] `uv run pytest` exits 0 with no failures
- [ ] All verification checks pass

## Save Command
```
git add tests/integration/test_chat_router.py tests/integration/test_router_registration.py tests/integration/test_goals_integration.py && git rm tests/integration/test_api.py tests/integration/test_full_conversation_flow.py tests/integration/test_full_collection_flow.py src/corpus_council/core/conversation.py src/corpus_council/core/collection.py && git commit -m "task-00006: update tests — integration tests for POST /chat, remove old endpoint tests"
```
