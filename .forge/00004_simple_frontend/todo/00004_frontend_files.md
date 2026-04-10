# Task 00004 — Create `frontend/index.html`, `frontend/app.js`, `frontend/style.css`

## Agent
programmer

## Goal
Create the three static frontend files that implement the five-tab single-page application.
No framework, no build step. Files are served as-is by FastAPI's `StaticFiles` mount.

## Prerequisites
- Task 00003 must be complete (`frontend/` mount registered in `app.py`)

## Deliverables

### 1. `frontend/index.html`

Requirements:
- One `<link>` to Pico.css CDN (v2.x): `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css`
- One `<link rel="stylesheet" href="style.css">`
- One `<script src="app.js" defer></script>` at end of `<body>`
- Five tab buttons using `data-tab="query"`, `data-tab="conversation"`, `data-tab="collection"`, `data-tab="files"`, `data-tab="admin"`
- Five `<section id="tab-query">`, `<section id="tab-conversation">`, etc.

**Query tab** contents:
- `<select id="goal-select">` — populated from goals manifest
- `<select id="query-mode">` with options: `<option value="">Default</option>`, `<option value="sequential">Sequential</option>`, `<option value="consolidated">Consolidated</option>`
- `<textarea id="query-input" placeholder="Enter your question..."></textarea>`
- `<button id="query-submit">Submit</button>`
- `<div id="query-response"></div>`

**Conversation tab** contents:
- `<input id="user-id" type="text" placeholder="User ID">`
- `<select id="conv-mode">` with same three options as query-mode
- `<div id="conv-history"></div>`
- `<textarea id="conv-input" placeholder="Type your message..."></textarea>`
- `<button id="conv-submit">Send</button>`

**Collection tab** contents:
- `<select id="plan-select">` — populated from `/files/plans`
- `<select id="coll-mode">` with same three options
- `<div id="coll-prompt"></div>`
- `<textarea id="coll-input" placeholder="Your response..."></textarea>`
- `<button id="coll-submit">Start Collection</button>`

**Files tab** contents:
- `<nav id="file-breadcrumb" aria-label="breadcrumb"></nav>`
- `<div id="file-tree"></div>`
- `<div id="file-editor" style="display:none">`
  - `<textarea id="file-content"></textarea>`
  - `<span id="unsaved-indicator" style="display:none">(unsaved)</span>`
  - `<button id="file-save">Save</button>`
  - `<button id="file-delete">Delete</button>`
- `<details id="new-file-form">`
  - `<summary>New file</summary>`
  - `<input id="new-file-name" type="text" placeholder="filename.md">`
  - `<button id="new-file-create">Create</button>`

**Admin tab** contents:
- `<textarea id="config-editor"></textarea>`
- `<button id="config-save">Save Config</button>`
- `<button id="config-reload">Reload</button>`
- `<div role="group">`
  - `<button id="btn-ingest">Ingest Corpus</button>`
  - `<button id="btn-embed">Embed Corpus</button>`
  - `<button id="btn-process-goals">Process Goals</button>`
- `<div id="admin-output"></div>`

### 2. `frontend/app.js`

Requirements (plain ES6+, no `import`/`export`, no frameworks):

**Tab switching**
```javascript
// On DOMContentLoaded:
// 1. Hide all sections except the first.
// 2. document.querySelectorAll('[data-tab]') — add click handlers.
// 3. Active tab button gets aria-current="page".
```

**On page load** (inside `DOMContentLoaded`):
- `loadGoals()` — fetch `/goals_manifest.json` (relative URL), populate `#goal-select`;
  on failure show `<option disabled>No goals available</option>`.
- `loadPlans()` — fetch `/files/plans`, iterate `entries`, populate `#plan-select` with
  filename without extension; on failure show `<option disabled>No plans available</option>`.
- Load `userId` from `localStorage.getItem('userId')`, set `#user-id` value.
- Load file tree roots on Files tab first-activate (lazy, not on page load).
- Load config on Admin tab first-activate (lazy).

**Query tab**:
```javascript
document.getElementById('query-submit').addEventListener('click', async () => {
  const btn = document.getElementById('query-submit');
  const responseDiv = document.getElementById('query-response');
  btn.setAttribute('aria-busy', 'true');
  btn.disabled = true;
  try {
    const res = await fetch('/query', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        goal: document.getElementById('goal-select').value,
        message: document.getElementById('query-input').value,
        mode: document.getElementById('query-mode').value || undefined,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      responseDiv.textContent = `Error: ${data.error || data.detail || res.status}`;
    } else {
      responseDiv.textContent = data.response;
    }
  } catch (err) {
    responseDiv.textContent = `Network error: ${err.message}`;
  } finally {
    btn.removeAttribute('aria-busy');
    btn.disabled = false;
  }
});
```

**Conversation tab**:
- Save `user-id` value to `localStorage('userId')` on input change.
- On submit: POST `/conversation` with `{user_id, message, mode}`; append user message as
  `<div class="user-turn">` and assistant response as `<div class="assistant-turn">` to
  `#conv-history`; disable submit while in flight.

**Collection tab**:
- `collSession = null` (module-level state).
- Button label: "Start Collection" when `collSession === null`, "Submit Response" otherwise.
- On click when `collSession === null`: POST `/collection/start` with
  `{user_id: localStorage.getItem('userId') || 'anonymous', plan_id, mode}`;
  store `{session_id, user_id}` in `collSession`; display `first_prompt` in `#coll-prompt`.
- On click when active: POST `/collection/respond` with `{user_id, session_id, message}`;
  display next `prompt` or "Collection complete" when `status === 'complete'`; reset
  `collSession = null` on complete.

**Files tab**:
- `currentFilePath = null` — tracks the path of the open file.
- `loadFileRoots()` — fetch `/files`, render buttons for each root in `#file-tree`.
- `loadDir(path)` — fetch `/files/{path}`, render entries as clickable items.
- `loadFile(path)` — fetch `/files/{path}`, populate `#file-content`, show `#file-editor`,
  set `currentFilePath = path`.
- Breadcrumb: render `<nav id="file-breadcrumb">` as clickable segments on every navigate.
- `#file-content` `input` event: show `#unsaved-indicator` if value differs from loaded content.
- Save: `PUT /files/{currentFilePath}` with `{content}`.
- Delete: `window.confirm("Delete <filename>?")` → `DELETE /files/{currentFilePath}` → reload parent dir.
- New file: `POST /files/{parentPath}/{name}` with `{content: ''}` → reload dir.

**Admin tab**:
- `loadConfig()` — `GET /config`, populate `#config-editor`.
- Save: `PUT /config` with `{content}`, show "Saved." in `#admin-output`.
- Ingest: POST `/corpus/ingest` with `{path: '.'}` (or omit body — check existing endpoint),
  show `chunks_created` in `#admin-output`.
- Embed: POST `/corpus/embed`, show `vectors_created`.
- Process Goals: POST `/admin/goals/process`, show `goals_processed`.
- Each trigger button: set `aria-busy="true"` while in flight.

**Admin tab lazy load**: first time user clicks "Admin" tab, call `loadConfig()`.
**Files tab lazy load**: first time user clicks "Files" tab, call `loadFileRoots()`.

### 3. `frontend/style.css`

Minimal overrides only:

```css
/* Tab navigation */
[data-tab] { cursor: pointer; }
[data-tab][aria-current="page"] { font-weight: bold; }

/* Conversation history */
#conv-history {
  max-height: 400px;
  overflow-y: auto;
  padding: 0.5rem;
}
.user-turn { text-align: right; margin: 0.25rem 0; }
.assistant-turn { text-align: left; margin: 0.25rem 0; }

/* File editor */
#file-content { width: 100%; min-height: 300px; font-family: monospace; }
#file-tree { margin-bottom: 1rem; }

/* Response areas */
#query-response { white-space: pre-wrap; }
#admin-output { white-space: pre-wrap; }

/* Unsaved indicator */
#unsaved-indicator { color: var(--pico-del-color, red); margin-left: 0.5rem; }
```

## Implementation Notes

- Existing endpoint `POST /corpus/ingest` requires `{"path": str}` (see `CorpusIngestRequest`
  in `models.py`). The Admin tab "Ingest" button should send the corpus directory path.
  Since the frontend cannot know the server-side path, send `{"path": "."}` and note this
  may fail if the corpus dir is not `.` — this is acceptable for a reference UI.
  Alternatively, fetch `GET /files` to list roots and display them; use the corpus root for ingest.
  The simplest correct approach: send `{"path": "."}` and display the raw error if it fails.
- Goals manifest URL: `GET /goals_manifest.json` — this file is served from the project root
  if present, or may 404. The JS must handle 404 gracefully.
- No module-level `import` statements in `app.js` — plain script, no ES modules.

## Verification

```bash
# File existence
test -f frontend/index.html && echo "index.html ok"
test -f frontend/app.js && echo "app.js ok"
test -f frontend/style.css && echo "style.css ok"

# No framework imports
! grep -q "import React\|import Vue\|import Angular" frontend/app.js && echo "no frameworks"

# Required JS patterns
grep -q "aria-busy" frontend/app.js && echo "aria-busy present"
grep -q "localStorage" frontend/app.js && echo "localStorage present"
grep -q "window.confirm" frontend/app.js && echo "confirm present"
grep -q "breadcrumb" frontend/app.js && echo "breadcrumb present"
```

## Save Command

```bash
test -f frontend/index.html && test -f frontend/app.js && test -f frontend/style.css && echo "frontend files ok"
```

Must print `frontend files ok` and exit 0.
