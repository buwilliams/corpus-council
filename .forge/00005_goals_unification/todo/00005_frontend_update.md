# Task 00005: Update frontend — 3-tab Goals/Files/Admin layout

## Role
programmer

## Objective
Replace the current 5-tab frontend (Query, Conversation, Collection, Files, Admin) with a 3-tab layout (Goals, Files, Admin) in `frontend/index.html` and `frontend/app.js`. The Goals tab calls `POST /chat`. The Files and Admin tabs preserve existing functionality unchanged.

## Context

**Files to modify:**
- `frontend/index.html`
- `frontend/app.js`

**Dependency:** Task 00003 established `POST /chat` as the only conversational endpoint.

**Current state:**
- `frontend/index.html`: 5 tabs — Query, Conversation, Collection, Files, Admin
- `frontend/app.js`: `initQueryTab()`, `initConversationTab()`, `initCollectionTab()`, `initFilesTab()`, `initAdminTab()`, `loadGoals()`, `loadPlans()`

---

### index.html changes

Replace the nav and tab sections. New layout:

**Nav (3 tabs):**
```html
<nav>
  <ul>
    <li><button data-tab="goals" aria-current="page">Goals</button></li>
    <li><button data-tab="files">Files</button></li>
    <li><button data-tab="admin">Admin</button></li>
  </ul>
</nav>
```

**Goals tab (`id="tab-goals"`):**
```html
<section id="tab-goals">
  <h2>Goals</h2>

  <label for="goal-select">Goal</label>
  <select id="goal-select">
    <option value="">Loading goals...</option>
  </select>

  <label for="goals-user-id">User ID</label>
  <input id="goals-user-id" type="text" placeholder="User ID">

  <label for="goals-conversation-id">Conversation ID</label>
  <input id="goals-conversation-id" type="text" placeholder="Auto-populated on first send, or enter existing ID">

  <label for="goals-mode">Mode</label>
  <select id="goals-mode">
    <option value="">Default</option>
    <option value="sequential">Sequential</option>
    <option value="consolidated">Consolidated</option>
  </select>

  <div id="goals-history" style="max-height:400px; overflow-y:auto; border:1px solid #ccc; padding:0.5rem; margin-bottom:0.5rem;"></div>

  <label for="goals-input">Message</label>
  <textarea id="goals-input" placeholder="Type your message..."></textarea>

  <button id="goals-submit">Send</button>
</section>
```

**Files tab** — unchanged from current `id="tab-files"` content. Keep all elements.

**Admin tab** — unchanged from current `id="tab-admin"` content.

**Remove:** The `id="tab-query"`, `id="tab-conversation"`, `id="tab-collection"` sections entirely.

---

### app.js changes

**Remove entirely:**
- `initQueryTab()` function
- `initConversationTab()` function
- `initCollectionTab()` function
- `updateCollButton()` function
- `loadPlans()` function
- `collSession` module-level variable

**Keep entirely (unchanged):**
- `initFilesTab()` and all file-related helpers (`loadFileRoots`, `loadDir`, `loadFile`, `renderEntry`, `renderBreadcrumb`, `encodePathSegments`)
- `initAdminTab()` and `loadConfig()` and `adminAction()`

**Update `loadGoals()`:** The existing `loadGoals()` reads from `GET /goals` and populates `#goal-select`. Keep this function. The element id `goal-select` is preserved in the new Goals tab.

**New `initGoalsTab()` function:**
```javascript
function initGoalsTab() {
  document.getElementById('goals-submit').addEventListener('click', async () => {
    const btn = document.getElementById('goals-submit');
    const history = document.getElementById('goals-history');
    const input = document.getElementById('goals-input');
    const message = input.value.trim();
    if (!message) return;

    const goal = document.getElementById('goal-select').value;
    const userId = document.getElementById('goals-user-id').value.trim();
    const convIdInput = document.getElementById('goals-conversation-id');
    const conversationId = convIdInput.value.trim() || null;
    const modeVal = document.getElementById('goals-mode').value;

    // Append user message to history
    const userDiv = document.createElement('div');
    userDiv.className = 'user-turn';
    userDiv.textContent = message;
    history.appendChild(userDiv);
    input.value = '';
    history.scrollTop = history.scrollHeight;

    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    try {
      const body = { goal, user_id: userId, message };
      if (conversationId) body.conversation_id = conversationId;
      if (modeVal) body.mode = modeVal;

      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      const assistantDiv = document.createElement('div');
      assistantDiv.className = 'assistant-turn';
      if (!res.ok) {
        assistantDiv.textContent = `Error: ${data.error || data.detail || res.status}`;
      } else {
        assistantDiv.textContent = data.response;
        // Auto-populate conversation_id on first response
        if (!convIdInput.value.trim()) {
          convIdInput.value = data.conversation_id;
        }
      }
      history.appendChild(assistantDiv);
      history.scrollTop = history.scrollHeight;
    } catch (err) {
      const errDiv = document.createElement('div');
      errDiv.className = 'assistant-turn';
      errDiv.textContent = `Network error: ${err.message}`;
      history.appendChild(errDiv);
    } finally {
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
    }
  });
}
```

**Update the tab-switching `initTabs()` function:**
- Module-level state `filesTabLoaded` and `adminTabLoaded` remain
- Remove the `filesTabLoaded` check from `query` and `conversation` load targets — they don't exist anymore
- Add goals tab as the default first active tab

**Update `DOMContentLoaded` handler:**
Remove calls to `initQueryTab()`, `initConversationTab()`, `initCollectionTab()`, and `loadPlans()`.
Add call to `initGoalsTab()`.
Remove restoration of `userId` from localStorage (it was for the conversation tab's `#user-id` input; the new goals tab uses `#goals-user-id` — no localStorage persistence needed, but it can be added optionally).

New `DOMContentLoaded`:
```javascript
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initGoalsTab();
  initFilesTab();
  initAdminTab();
  loadGoals();
});
```

**Module-level state cleanup:** Remove `let collSession = null;`.

**No new CDN links, no npm, no bundlers** — plain vanilla JS, Pico.css CDN link stays.

**Tech stack:** Vanilla HTML5/CSS3/ES6+, Pico.css via CDN (unchanged).

## Steps
1. Open `frontend/index.html`. Replace the `<nav>` block and all tab `<section>` elements with the 3-tab structure described above. Keep `<head>`, `<h1>`, and `<script>` tag unchanged.
2. Open `frontend/app.js`:
   a. Remove `let collSession = null;` from module state
   b. Remove `loadPlans()`, `initQueryTab()`, `initConversationTab()`, `initCollectionTab()`, `updateCollButton()`
   c. Add `initGoalsTab()` as described above
   d. Update `DOMContentLoaded` listener
3. Verify the HTML has exactly 3 tab buttons (`goals`, `files`, `admin`) and 3 sections (`tab-goals`, `tab-files`, `tab-admin`)
4. Verify `app.js` has no reference to `/query`, `/conversation`, `/collection`
5. Run `uv run ruff check . && uv run ruff format --check .` (Python files only — JS is not checked by ruff)
6. Run `uv run pyright src/` to confirm no regressions

## Verification
- `frontend/index.html` contains exactly 3 `data-tab` buttons: `goals`, `files`, `admin`
- `frontend/index.html` contains no `data-tab="query"`, no `data-tab="conversation"`, no `data-tab="collection"`
- `frontend/index.html` contains element `id="tab-goals"` with a `<select id="goal-select">` and a `<div id="goals-history">`
- `frontend/index.html` contains element `id="tab-files"` (unchanged file browser)
- `frontend/index.html` contains element `id="tab-admin"` (unchanged admin section)
- `frontend/app.js` contains no reference to `/query` endpoint
- `frontend/app.js` contains no reference to `/conversation` endpoint
- `frontend/app.js` contains no reference to `/collection/start` or `/collection/respond`
- `frontend/app.js` defines `initGoalsTab`
- `frontend/app.js` does not define `initQueryTab`
- `frontend/app.js` does not define `initConversationTab`
- `frontend/app.js` does not define `initCollectionTab`
- `uv run pyright src/` exits 0
- `uv run ruff check . && uv run ruff format --check .` exits 0
- `pyproject.toml` is unchanged
- Dynamic: start, verify Goals tab elements exist in HTML, verify /chat is the only conversational endpoint, stop:
  ```bash
  uv run uvicorn corpus_council.api.app:app --port 8765 &
  APP_PID=$!
  for i in $(seq 1 15); do curl -sf http://localhost:8765/goals 2>/dev/null && break; sleep 1; [ $i -eq 15 ] && kill $APP_PID && exit 1; done
  curl -sf http://localhost:8765/openapi.json | python3 -c "
  import sys, json
  data = json.load(sys.stdin)
  paths = data.get('paths', {})
  assert '/chat' in paths, f'/chat missing from paths: {list(paths.keys())}'
  assert '/query' not in paths, f'/query still present'
  assert '/conversation' not in paths, f'/conversation still present'
  assert '/collection/start' not in paths, f'/collection/start still present'
  print('OK: only /chat as conversational endpoint')
  "
  grep -l 'goal-select' /home/buddy/projects/corpus-council/frontend/index.html && echo "OK: goal-select found in index.html"
  kill $APP_PID
  ```

## Done When
- [ ] `frontend/index.html` has 3-tab layout: Goals, Files, Admin
- [ ] `frontend/app.js` has `initGoalsTab()` calling `POST /chat`; no query/conversation/collection code remains
- [ ] All verification checks pass

## Save Command
```
git add frontend/index.html frontend/app.js && git commit -m "task-00005: update frontend — 3-tab Goals/Files/Admin layout"
```
