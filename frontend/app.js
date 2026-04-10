/* app.js — Corpus Council frontend, plain ES6+, no import/export, no frameworks */

// Module-level state
let collSession = null;
let currentFilePath = null;
let loadedFileContent = '';
let filesTabLoaded = false;
let adminTabLoaded = false;
let currentDirPath = '';

// ─── Tab switching ────────────────────────────────────────────────────────────

function initTabs() {
  const tabs = document.querySelectorAll('[data-tab]');
  const sections = document.querySelectorAll('section[id^="tab-"]');

  // Hide all sections except the first
  sections.forEach((sec, i) => {
    sec.style.display = i === 0 ? '' : 'none';
  });

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');

      // Hide all sections, deactivate all tabs
      sections.forEach(sec => { sec.style.display = 'none'; });
      tabs.forEach(t => { t.removeAttribute('aria-current'); });

      // Show target section, mark tab active
      const section = document.getElementById('tab-' + target);
      if (section) section.style.display = '';
      btn.setAttribute('aria-current', 'page');

      // Lazy loads
      if (target === 'files' && !filesTabLoaded) {
        filesTabLoaded = true;
        loadFileRoots();
      }
      if (target === 'admin' && !adminTabLoaded) {
        adminTabLoaded = true;
        loadConfig();
      }
    });
  });
}

// ─── Goals ────────────────────────────────────────────────────────────────────

async function loadGoals() {
  const sel = document.getElementById('goal-select');
  try {
    const res = await fetch('/goals_manifest.json');
    if (!res.ok) throw new Error('Failed to load goals');
    const goals = await res.json();
    sel.innerHTML = '';
    if (!goals || goals.length === 0) {
      sel.innerHTML = '<option disabled>No goals available</option>';
      return;
    }
    goals.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.name;
      opt.textContent = g.name;
      sel.appendChild(opt);
    });
  } catch (_err) {
    sel.innerHTML = '<option disabled>No goals available</option>';
  }
}

// ─── Plans ────────────────────────────────────────────────────────────────────

async function loadPlans() {
  const sel = document.getElementById('plan-select');
  try {
    const res = await fetch('/files/plans');
    if (!res.ok) throw new Error('Failed to load plans');
    const data = await res.json();
    const entries = data.entries || [];
    sel.innerHTML = '';
    if (entries.length === 0) {
      sel.innerHTML = '<option disabled>No plans available</option>';
      return;
    }
    entries.forEach(entry => {
      const name = entry.name || entry;
      const displayName = typeof name === 'string' ? name.replace(/\.[^.]+$/, '') : String(name);
      const opt = document.createElement('option');
      opt.value = displayName;
      opt.textContent = displayName;
      sel.appendChild(opt);
    });
  } catch (_err) {
    sel.innerHTML = '<option disabled>No plans available</option>';
  }
}

// ─── Query tab ────────────────────────────────────────────────────────────────

function initQueryTab() {
  document.getElementById('query-submit').addEventListener('click', async () => {
    const btn = document.getElementById('query-submit');
    const responseDiv = document.getElementById('query-response');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const body = {
        goal: document.getElementById('goal-select').value,
        message: document.getElementById('query-input').value,
      };
      const modeVal = document.getElementById('query-mode').value;
      if (modeVal) body.mode = modeVal;

      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
}

// ─── Conversation tab ─────────────────────────────────────────────────────────

function initConversationTab() {
  const userIdInput = document.getElementById('user-id');

  // Persist userId to localStorage on change
  userIdInput.addEventListener('input', () => {
    localStorage.setItem('userId', userIdInput.value);
  });

  document.getElementById('conv-submit').addEventListener('click', async () => {
    const btn = document.getElementById('conv-submit');
    const history = document.getElementById('conv-history');
    const input = document.getElementById('conv-input');
    const message = input.value.trim();
    if (!message) return;

    const userId = userIdInput.value || localStorage.getItem('userId') || 'anonymous';
    const modeVal = document.getElementById('conv-mode').value;

    // Append user message
    const userDiv = document.createElement('div');
    userDiv.className = 'user-turn';
    userDiv.textContent = message;
    history.appendChild(userDiv);
    input.value = '';
    history.scrollTop = history.scrollHeight;

    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    try {
      const body = { user_id: userId, message };
      if (modeVal) body.mode = modeVal;

      const res = await fetch('/conversation', {
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

// ─── Collection tab ───────────────────────────────────────────────────────────

function updateCollButton() {
  const btn = document.getElementById('coll-submit');
  btn.textContent = collSession === null ? 'Start Collection' : 'Submit Response';
}

function initCollectionTab() {
  document.getElementById('coll-submit').addEventListener('click', async () => {
    const btn = document.getElementById('coll-submit');
    const promptDiv = document.getElementById('coll-prompt');
    const input = document.getElementById('coll-input');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;

    try {
      if (collSession === null) {
        // Start a new session
        const planId = document.getElementById('plan-select').value;
        const modeVal = document.getElementById('coll-mode').value;
        const body = {
          user_id: localStorage.getItem('userId') || 'anonymous',
          plan_id: planId,
        };
        if (modeVal) body.mode = modeVal;

        const res = await fetch('/collection/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
          promptDiv.textContent = `Error: ${data.error || data.detail || res.status}`;
        } else {
          collSession = { session_id: data.session_id, user_id: body.user_id };
          promptDiv.textContent = data.first_prompt || data.prompt || '';
          input.value = '';
          updateCollButton();
        }
      } else {
        // Submit a response
        const message = input.value.trim();
        const res = await fetch('/collection/respond', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: collSession.user_id,
            session_id: collSession.session_id,
            message,
          }),
        });
        const data = await res.json();
        if (!res.ok) {
          promptDiv.textContent = `Error: ${data.error || data.detail || res.status}`;
        } else if (data.status === 'complete') {
          promptDiv.textContent = 'Collection complete';
          collSession = null;
          updateCollButton();
        } else {
          promptDiv.textContent = data.prompt || '';
          input.value = '';
        }
      }
    } catch (err) {
      promptDiv.textContent = `Network error: ${err.message}`;
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });
}

// ─── Files tab ────────────────────────────────────────────────────────────────

function renderBreadcrumb(path) {
  const nav = document.getElementById('file-breadcrumb');
  nav.innerHTML = '';

  // Root link
  const rootBtn = document.createElement('button');
  rootBtn.textContent = 'Root';
  rootBtn.classList.add('breadcrumb-item');
  rootBtn.addEventListener('click', () => {
    currentDirPath = '';
    loadFileRoots();
  });
  nav.appendChild(rootBtn);

  if (!path) return;

  const parts = path.split('/').filter(Boolean);
  let accumulated = '';
  parts.forEach((part, i) => {
    accumulated = accumulated ? accumulated + '/' + part : part;
    const sep = document.createTextNode(' / ');
    nav.appendChild(sep);

    const btn = document.createElement('button');
    btn.textContent = part;
    btn.classList.add('breadcrumb-item');
    const capPath = accumulated;
    if (i < parts.length - 1) {
      btn.addEventListener('click', () => {
        loadDir(capPath);
      });
    } else {
      btn.setAttribute('aria-current', 'page');
    }
    nav.appendChild(btn);
  });
}

async function loadFileRoots() {
  currentDirPath = '';
  renderBreadcrumb('');
  const tree = document.getElementById('file-tree');
  tree.innerHTML = 'Loading...';
  try {
    const res = await fetch('/files');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    tree.innerHTML = '';
    const entries = data.entries || data;
    if (!Array.isArray(entries) || entries.length === 0) {
      tree.textContent = 'No files found.';
      return;
    }
    entries.forEach(entry => {
      renderEntry(tree, entry, '');
    });
  } catch (err) {
    tree.textContent = `Error loading files: ${err.message}`;
  }
}

async function loadDir(path) {
  currentDirPath = path;
  renderBreadcrumb(path);
  // Hide file editor when navigating
  document.getElementById('file-editor').style.display = 'none';
  currentFilePath = null;

  const tree = document.getElementById('file-tree');
  tree.innerHTML = 'Loading...';
  try {
    const res = await fetch('/files/' + encodePathSegments(path));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    tree.innerHTML = '';
    const entries = data.entries || data;
    if (!Array.isArray(entries) || entries.length === 0) {
      tree.textContent = 'Empty directory.';
      return;
    }
    entries.forEach(entry => {
      renderEntry(tree, entry, path);
    });
  } catch (err) {
    tree.textContent = `Error: ${err.message}`;
  }
}

function renderEntry(container, entry, parentPath) {
  const btn = document.createElement('button');
  const name = entry.name || entry;
  const isDir = entry.is_dir || entry.type === 'directory';
  const entryPath = parentPath ? parentPath + '/' + name : name;

  btn.textContent = (isDir ? '📁 ' : '📄 ') + name;
  btn.style.display = 'block';
  btn.style.width = '100%';
  btn.style.textAlign = 'left';
  btn.style.marginBottom = '0.25rem';

  if (isDir) {
    btn.addEventListener('click', () => loadDir(entryPath));
  } else {
    btn.addEventListener('click', () => loadFile(entryPath));
  }
  container.appendChild(btn);
}

async function loadFile(path) {
  currentFilePath = path;
  renderBreadcrumb(path);

  try {
    const res = await fetch('/files/' + encodePathSegments(path));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const content = data.content !== undefined ? data.content : (typeof data === 'string' ? data : JSON.stringify(data, null, 2));
    loadedFileContent = content;
    const editor = document.getElementById('file-content');
    editor.value = content;
    document.getElementById('file-editor').style.display = '';
    document.getElementById('unsaved-indicator').style.display = 'none';
  } catch (err) {
    alert(`Error loading file: ${err.message}`);
  }
}

function encodePathSegments(path) {
  return path.split('/').map(encodeURIComponent).join('/');
}

function initFilesTab() {
  // Unsaved indicator on content change
  document.getElementById('file-content').addEventListener('input', () => {
    const indicator = document.getElementById('unsaved-indicator');
    const current = document.getElementById('file-content').value;
    indicator.style.display = current !== loadedFileContent ? '' : 'none';
  });

  // Save file
  document.getElementById('file-save').addEventListener('click', async () => {
    if (!currentFilePath) return;
    const btn = document.getElementById('file-save');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const content = document.getElementById('file-content').value;
      const res = await fetch('/files/' + encodePathSegments(currentFilePath), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(`Save failed: ${data.error || data.detail || res.status}`);
      } else {
        loadedFileContent = content;
        document.getElementById('unsaved-indicator').style.display = 'none';
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // Delete file
  document.getElementById('file-delete').addEventListener('click', async () => {
    if (!currentFilePath) return;
    const filename = currentFilePath.split('/').pop();
    if (!window.confirm(`Delete ${filename}?`)) return;

    const btn = document.getElementById('file-delete');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const res = await fetch('/files/' + encodePathSegments(currentFilePath), {
        method: 'DELETE',
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(`Delete failed: ${data.error || data.detail || res.status}`);
      } else {
        document.getElementById('file-editor').style.display = 'none';
        currentFilePath = null;
        loadedFileContent = '';
        // Reload parent directory
        if (currentDirPath) {
          loadDir(currentDirPath);
        } else {
          loadFileRoots();
        }
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // New file
  document.getElementById('new-file-create').addEventListener('click', async () => {
    const nameInput = document.getElementById('new-file-name');
    const name = nameInput.value.trim();
    if (!name) { alert('Enter a filename.'); return; }

    const parentPath = currentDirPath || '';
    const fullPath = parentPath ? parentPath + '/' + name : name;
    const btn = document.getElementById('new-file-create');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const res = await fetch('/files/' + encodePathSegments(fullPath), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: '' }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(`Create failed: ${data.error || data.detail || res.status}`);
      } else {
        nameInput.value = '';
        document.getElementById('new-file-form').removeAttribute('open');
        if (parentPath) {
          loadDir(parentPath);
        } else {
          loadFileRoots();
        }
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });
}

// ─── Admin tab ────────────────────────────────────────────────────────────────

async function loadConfig() {
  const editor = document.getElementById('config-editor');
  try {
    const res = await fetch('/config');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    editor.value = data.content !== undefined ? data.content : JSON.stringify(data, null, 2);
  } catch (err) {
    editor.value = `# Error loading config: ${err.message}`;
  }
}

async function adminAction(url, body, successFn) {
  const output = document.getElementById('admin-output');
  output.textContent = 'Working...';
  try {
    const fetchOpts = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    };
    if (body !== null) fetchOpts.body = JSON.stringify(body);

    const res = await fetch(url, fetchOpts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      output.textContent = `Error: ${data.error || data.detail || res.status}`;
    } else {
      output.textContent = successFn(data);
    }
  } catch (err) {
    output.textContent = `Network error: ${err.message}`;
  }
}

function initAdminTab() {
  // Save config
  document.getElementById('config-save').addEventListener('click', async () => {
    const btn = document.getElementById('config-save');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    const output = document.getElementById('admin-output');
    try {
      const content = document.getElementById('config-editor').value;
      const res = await fetch('/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        output.textContent = `Save failed: ${data.error || data.detail || res.status}`;
      } else {
        output.textContent = 'Saved.';
      }
    } catch (err) {
      output.textContent = `Network error: ${err.message}`;
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // Reload config
  document.getElementById('config-reload').addEventListener('click', async () => {
    const btn = document.getElementById('config-reload');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      await loadConfig();
      document.getElementById('admin-output').textContent = 'Config reloaded.';
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // Ingest corpus
  document.getElementById('btn-ingest').addEventListener('click', async () => {
    const btn = document.getElementById('btn-ingest');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      await adminAction('/corpus/ingest', { path: '.' }, data =>
        `Ingest complete. Chunks created: ${data.chunks_created !== undefined ? data.chunks_created : JSON.stringify(data)}`
      );
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // Embed corpus
  document.getElementById('btn-embed').addEventListener('click', async () => {
    const btn = document.getElementById('btn-embed');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      await adminAction('/corpus/embed', null, data =>
        `Embed complete. Vectors created: ${data.vectors_created !== undefined ? data.vectors_created : JSON.stringify(data)}`
      );
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });

  // Process goals
  document.getElementById('btn-process-goals').addEventListener('click', async () => {
    const btn = document.getElementById('btn-process-goals');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      await adminAction('/admin/goals/process', null, data =>
        `Goals processed: ${data.goals_processed !== undefined ? data.goals_processed : JSON.stringify(data)}`
      );
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initQueryTab();
  initConversationTab();
  initCollectionTab();
  initFilesTab();
  initAdminTab();

  // Load goals and plans on startup
  loadGoals();
  loadPlans();

  // Restore userId from localStorage
  const savedUserId = localStorage.getItem('userId');
  if (savedUserId) {
    document.getElementById('user-id').value = savedUserId;
  }
});
