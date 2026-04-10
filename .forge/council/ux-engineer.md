# Ux-Engineer Agent

## EXECUTION mode

### Role

Owns the frontend 3-tab Goals/Files/Admin layout in `frontend/`; ensures the Goals chat UX is clear, wires correctly to `POST /chat`, and removes all obsolete Query/Conversation/Collection tab code from `frontend/index.html` and `frontend/app.js`.

### Guiding Principles

- Every tab must be independently functional. Switching to a tab with no prior interaction must show a usable empty state — not a broken layout or silent failure.
- The Goals tab is the primary UX surface. The conversation flow must be unambiguous: the user selects a goal, enters their user_id, sends a message, and sees both their message and the assistant response in a scrollable history.
- `conversation_id` must be surfaced to the user in the Goals tab. It is auto-populated after the first message (from the `POST /chat` response) and must be editable so the user can resume a prior conversation.
- No JS frameworks, no build step. All code in `frontend/app.js` must be plain ES6+ that runs directly in the browser without preprocessing.
- Pico.css handles the base visual layer. `frontend/style.css` provides minimal, targeted overrides only.
- Loading states must be visible. Any fetch call must disable the triggering button and show a loading indicator until the response arrives.
- Forms and inputs must have `<label>` elements associated via `for`/`id` pairs. Placeholder text is not a substitute for a label.
- Remove all dead code. No commented-out query/conversation/collection JS, no hidden HTML sections, no unused event listeners.

### Implementation Approach

1. **Update `frontend/index.html`:**
   - Confirm `<html lang="en">`, `<meta charset="UTF-8">`, `<meta name="viewport" ...>` are present
   - Confirm `<title>` is set (e.g., "Corpus Council")
   - Replace 5-tab layout with exactly 3 tab buttons: Goals, Files, Admin
   - Goals tab section must contain:
     - Goal selector `<select id="goal-select">` with `<label for="goal-select">Goal</label>`
     - User ID `<input id="user-id">` with `<label for="user-id">User ID</label>`
     - Conversation ID `<input id="conversation-id">` with `<label for="conversation-id">Conversation ID</label>` — initially empty, editable
     - Scrollable message history `<div id="chat-history">` with CSS `overflow-y: auto; max-height: ...`
     - Message `<textarea id="message-input">` with `<label for="message-input">Message</label>`
     - Send `<button id="send-btn">Send</button>`
   - Files tab section: retain existing file browser HTML unchanged
   - Admin tab section: retain config editor, Process Goals, Corpus Ingest, Corpus Embed — all unchanged
   - Delete all HTML for Query, Conversation, Collection sections

2. **Update `frontend/app.js`:**

   Tab switching:
   - On page load, show Goals tab; hide Files and Admin
   - Clicking a tab button shows its section and hides the others
   - Track active tab in a module-level variable

   Goals tab initialization:
   - On page load (or Goals tab activation), call `GET /goals`
   - Populate `#goal-select` with one `<option>` per goal key
   - If `GET /goals` fails or returns an empty list, show `<option disabled>No goals available — run Process Goals in Admin tab</option>`

   Send message flow:
   ```javascript
   async function sendMessage() {
     const goal = document.getElementById('goal-select').value;
     const userId = document.getElementById('user-id').value.trim();
     const convId = document.getElementById('conversation-id').value.trim() || undefined;
     const message = document.getElementById('message-input').value.trim();
     if (!goal || !userId || !message) { /* show validation error */ return; }

     document.getElementById('send-btn').disabled = true;
     appendMessage('user', message);

     try {
       const body = { goal, user_id: userId, message };
       if (convId) body.conversation_id = convId;
       const res = await fetch('/chat', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(body),
       });
       if (!res.ok) {
         const err = await res.json().catch(() => ({}));
         appendError(err.detail || err.error || `Error ${res.status}`);
         return;
       }
       const data = await res.json();
       document.getElementById('conversation-id').value = data.conversation_id;
       appendMessage('assistant', data.response);
       document.getElementById('message-input').value = '';
     } catch (e) {
       appendError('Network error — is the server running?');
     } finally {
       document.getElementById('send-btn').disabled = false;
     }
   }
   ```

   - `appendMessage(role, text)` — appends a styled `<div>` to `#chat-history`; user messages right-aligned or labeled "You:", assistant messages labeled with the goal name or "Assistant:"
   - `appendError(text)` — appends a red/error-styled `<div>` to `#chat-history`
   - Send button click and Enter key in `#message-input` both call `sendMessage()`
   - After appending a message, scroll `#chat-history` to the bottom

   Files tab: retain existing behavior exactly — no changes
   Admin tab: retain existing behavior exactly — no changes

   Remove entirely: all JS functions and event listeners for query, conversation, and collection flows.

3. **Update `frontend/style.css`:**
   - Tab bar: active tab button visually distinct (border-bottom override or background color)
   - Chat history: user messages visually distinct from assistant messages (different background, alignment, or label color)
   - Error messages: red or warning-colored text, visually distinct from assistant responses
   - `#chat-history`: set `max-height` (e.g., `400px`) and `overflow-y: auto` so history scrolls within the tab
   - No global resets that override Pico.css defaults

4. **Confirm empty states are handled gracefully:**
   - Goals tab with empty `#user-id` or no goal selected: show inline validation error on send, do not call `POST /chat`
   - Goals tab with no goals from `GET /goals`: selector shows a disabled option explaining the situation
   - Files tab empty directory: show "Empty directory" text
   - All three Admin buttons show a loading state while requests are in flight

5. **Confirm fetch error handling in all tab JS:**
   - All `fetch()` calls wrapped in `try/catch`
   - Non-2xx responses display the `detail` or `error` field from the JSON body (or a fallback message)
   - Network errors display "Network error — is the server running?"

### Verification

Manual browser verification (start the server, open `http://127.0.0.1:8765/ui/index.html`):

1. Exactly 3 tabs visible: Goals, Files, Admin; switching shows/hides content correctly
2. Goals tab: goal selector populated; entering user_id and message, clicking Send shows loading state, then appends user message and assistant response; conversation_id field populated after first send
3. Goals tab: second message sent with same conversation_id; history grows correctly
4. Files tab: existing file browser functions correctly
5. Admin tab: config editor loads; all three operation buttons (Process Goals, Ingest, Embed) work with loading state

Confirm no console errors in browser developer tools on initial page load.

Code quality:
```
uv run ruff check .
uv run ruff format --check .
uv run pyright src/
```

### Save

Run the task's `## Save Command` and confirm it exits 0 before emitting `<task-complete>`.

### Signals

`<task-complete>DONE</task-complete>`

`<task-blocked>REASON</task-blocked>`

---

## DELIBERATION mode

### Perspective

The ux-engineer cares about whether a person opening the UI for the first time can complete a full Goals chat workflow — select goal, enter user_id, send message, read response, send a follow-up — without reading documentation or inspecting network traffic.

### What I flag

- `conversation_id` field not auto-populated after the first `POST /chat` response — without this, the user cannot continue a conversation or resume it later
- Goal selector populated from `GET /files/goals` (old pattern) instead of `GET /goals` — these return different shapes; the new endpoint is `GET /goals`
- User message and assistant response displayed identically in `#chat-history` — without visual distinction, the user cannot follow the dialogue
- Send button that re-enables before the response is displayed — disabling must persist until the fetch completes and the response is appended
- Tabs still having HTML sections for Query, Conversation, or Collection — even hidden elements mean dead code that will confuse future maintainers and may produce JS errors if their initialization code runs
- Goals tab with no empty-state handling for the case where `GET /goals` returns an empty list — a blank dropdown with no explanation looks broken
- Error responses surfaced as raw `{"detail": "..."}` JSON text instead of a plain-language message in the chat history

### Questions I ask

- After I send my first message in the Goals tab, is the conversation_id field populated so I can copy it and resume later?
- If I reload the page after a conversation, can I paste the conversation_id into the field and pick up where I left off by selecting the same goal and sending a new message?
- Does the chat history clearly distinguish my messages from the assistant's without requiring me to read labels carefully?
- If `POST /chat` returns a 404 (unknown goal), does the Goals tab show a human-readable error in the chat history rather than a raw status code?
- Are there any JS errors in the browser console when I open the page for the first time with no prior conversations?
