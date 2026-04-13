/* app.js — Corpus Council frontend, plain ES6+, no import/export, no frameworks */

// Module-level state
let currentFilePath = null;
let loadedFileContent = '';
let filesTabLoaded = false;
let adminTabLoaded = false;
let currentDirPath = '';
let currentConversationId = null;

// ─── Tab switching ────────────────────────────────────────────────────────────

function initTabs() {
  const hamburger = document.getElementById('hamburger');
  const menu = document.getElementById('hamburger-menu');
  const backdrop = document.getElementById('menu-backdrop');
  const tabs = document.querySelectorAll('[data-tab]');
  const sections = document.querySelectorAll('section[id^="tab-"]');

  // Hide all sections except the first
  sections.forEach((sec, i) => {
    sec.style.display = i === 0 ? '' : 'none';
  });

  function setTitle(tabName) {
    const label = tabName.charAt(0).toUpperCase() + tabName.slice(1);
    document.getElementById('app-title').textContent = label + ' \u2014 Corpus Council';
  }

  function openMenu() {
    menu.classList.add('open');
    backdrop.classList.add('open');
    hamburger.setAttribute('aria-expanded', 'true');
  }

  function closeMenu() {
    menu.classList.remove('open');
    backdrop.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
  }

  hamburger.addEventListener('click', () => {
    menu.classList.contains('open') ? closeMenu() : openMenu();
  });

  backdrop.addEventListener('click', closeMenu);

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');

      closeMenu();

      sections.forEach(sec => { sec.style.display = 'none'; });
      tabs.forEach(t => { t.removeAttribute('aria-current'); });

      const section = document.getElementById('tab-' + target);
      if (section) section.style.display = '';
      btn.setAttribute('aria-current', 'page');
      setTitle(target);

      if (target === 'files' && !filesTabLoaded) {
        filesTabLoaded = true;
        loadFileRoots();
      }
      if (target === 'admin' && !adminTabLoaded) {
        adminTabLoaded = true;
      }
    });
  });
}

// ─── Goals ────────────────────────────────────────────────────────────────────

async function loadGoals() {
  const sel = document.getElementById('goal-select');
  try {
    const res = await fetch('/goals');
    if (!res.ok) throw new Error('Failed to load goals');
    const data = await res.json();
    const goals = data.goals || [];
    sel.innerHTML = '';
    if (goals.length === 0) {
      sel.innerHTML = '<option disabled>No goals available</option>';
      return;
    }
    goals.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.name;
      opt.textContent = g.name;
      sel.appendChild(opt);
    });
    // Restore saved goal selection
    const savedGoal = localStorage.getItem('cc-goal');
    if (savedGoal && goals.some(g => g.name === savedGoal)) {
      sel.value = savedGoal;
    }
  } catch (_err) {
    sel.innerHTML = '<option disabled>No goals available</option>';
  }
  // Restore saved user ID and mode
  const savedUserId = localStorage.getItem('cc-user-id');
  if (savedUserId) document.getElementById('goals-user-id').value = savedUserId;
  const savedMode = localStorage.getItem('cc-mode');
  if (savedMode) document.getElementById('goals-mode').value = savedMode;
  refreshConversationList();
}

// ─── Goals tab ────────────────────────────────────────────────────────────────

function initGoalsTab() {
  document.getElementById('goal-select').addEventListener('change', () => {
    localStorage.setItem('cc-goal', document.getElementById('goal-select').value);
    refreshConversationList();
  });
  document.getElementById('goals-user-id').addEventListener('change', () => {
    localStorage.setItem('cc-user-id', document.getElementById('goals-user-id').value.trim());
    refreshConversationList();
  });
  document.getElementById('goals-mode').addEventListener('change', () => {
    localStorage.setItem('cc-mode', document.getElementById('goals-mode').value);
  });
  document.getElementById('goals-new-conv').addEventListener('click', toggleNewConvForm);
  document.getElementById('goals-submit').addEventListener('click', sendGoalMessage);
}

function toggleNewConvForm() {
  const form = document.getElementById('new-conv-form');
  const open = form.style.display !== 'none';
  form.style.display = open ? 'none' : '';
  if (!open) {
    // Opened form — deselect active conversation
    currentConversationId = null;
    document.getElementById('goals-history').innerHTML = '';
    document.getElementById('goals-meta').innerHTML = '';
    document.querySelectorAll('.conv-item').forEach(item => item.classList.remove('active'));
  }
}

function updateMeta(goal, userId, mode, conversationId) {
  const meta = document.getElementById('goals-meta');
  meta.innerHTML = '';
  [
    ['Goal', goal],
    ['User', userId],
    ['Mode', mode || 'default'],
    ['Conv', conversationId ? conversationId.slice(0, 8) + '\u2026' : '\u2014'],
  ].forEach(([label, value]) => {
    const span = document.createElement('span');
    const b = document.createElement('b');
    b.textContent = label + ':';
    span.appendChild(b);
    span.appendChild(document.createTextNode(' ' + value));
    meta.appendChild(span);
  });
}

async function refreshConversationList() {
  const goal = document.getElementById('goal-select').value;
  const userId = document.getElementById('goals-user-id').value.trim();
  const list = document.getElementById('goals-conv-list');

  if (!goal || !userId || userId.length < 4) {
    list.innerHTML = '<div class="conv-item-empty">Set goal and user ID</div>';
    return;
  }

  try {
    const res = await fetch(
      `/conversations?user_id=${encodeURIComponent(userId)}&goal=${encodeURIComponent(goal)}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    list.innerHTML = '';
    if (data.conversations.length === 0) {
      list.innerHTML = '<div class="conv-item-empty">No conversations yet</div>';
      return;
    }

    data.conversations.forEach(conv => {
      const item = document.createElement('div');
      item.className = 'conv-item' + (conv.conversation_id === currentConversationId ? ' active' : '');
      item.dataset.convId = conv.conversation_id;

      const label = document.createElement('span');
      label.className = 'conv-item-label';
      label.textContent = conv.conversation_id.slice(0, 8) + '\u2026';
      label.title = conv.conversation_id;
      label.addEventListener('click', () => loadConversation(conv.conversation_id));

      const del = document.createElement('button');
      del.className = 'conv-delete';
      del.textContent = '\u00d7';
      del.title = 'Delete';
      del.addEventListener('click', e => { e.stopPropagation(); deleteConversation(conv.conversation_id); });

      item.appendChild(label);
      item.appendChild(del);
      list.appendChild(item);
    });
  } catch (err) {
    list.innerHTML = `<div class="conv-item-empty">Error: ${err.message}</div>`;
  }
}

async function loadConversation(conversationId) {
  const goal = document.getElementById('goal-select').value;
  const userId = document.getElementById('goals-user-id').value.trim();
  const mode = document.getElementById('goals-mode').value;

  currentConversationId = conversationId;
  document.getElementById('new-conv-form').style.display = 'none';
  updateMeta(goal, userId, mode, conversationId);

  document.querySelectorAll('.conv-item').forEach(item => {
    item.classList.toggle('active', item.dataset.convId === conversationId);
  });

  const history = document.getElementById('goals-history');
  history.innerHTML = '<div class="conv-item-empty">Loading\u2026</div>';

  try {
    const res = await fetch(
      `/conversations/${encodeURIComponent(conversationId)}?user_id=${encodeURIComponent(userId)}&goal=${encodeURIComponent(goal)}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    history.innerHTML = '';
    data.messages.forEach(msg => {
      const userDiv = document.createElement('div');
      userDiv.className = 'user-turn';
      userDiv.textContent = msg.user;
      history.appendChild(userDiv);

      const assistantDiv = document.createElement('div');
      assistantDiv.className = 'assistant-turn';
      assistantDiv.innerHTML = marked.parse(msg.assistant);
      history.appendChild(assistantDiv);
    });
    history.scrollTop = history.scrollHeight;
  } catch (err) {
    history.innerHTML = `<div class="conv-item-empty">Error: ${err.message}</div>`;
  }
}

async function deleteConversation(conversationId) {
  const goal = document.getElementById('goal-select').value;
  const userId = document.getElementById('goals-user-id').value.trim();
  if (!goal || !userId) return;
  if (!confirm('Delete this conversation?')) return;

  try {
    const res = await fetch(
      `/conversations/${encodeURIComponent(conversationId)}?user_id=${encodeURIComponent(userId)}&goal=${encodeURIComponent(goal)}`,
      { method: 'DELETE' }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    if (conversationId === currentConversationId) {
      currentConversationId = null;
      document.getElementById('goals-history').innerHTML = '';
      document.getElementById('goals-meta').innerHTML = '';
    }
    refreshConversationList();
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
  }
}

async function sendGoalMessage() {
  const btn = document.getElementById('goals-submit');
  const history = document.getElementById('goals-history');
  const input = document.getElementById('goals-input');
  const message = input.value.trim();
  if (!message) return;

  const goal = document.getElementById('goal-select').value;
  const userId = document.getElementById('goals-user-id').value.trim();
  const modeVal = document.getElementById('goals-mode').value;

  const userDiv = document.createElement('div');
  userDiv.className = 'user-turn';
  userDiv.textContent = message;
  history.appendChild(userDiv);
  input.value = '';
  history.scrollTop = history.scrollHeight;

  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'assistant-turn loading-turn';
  loadingDiv.textContent = 'Loading…';
  history.appendChild(loadingDiv);
  history.scrollTop = history.scrollHeight;

  btn.disabled = true;
  btn.setAttribute('aria-busy', 'true');

  try {
    const body = { goal, user_id: userId, message };
    if (currentConversationId) body.conversation_id = currentConversationId;
    if (modeVal) body.mode = modeVal;

    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    loadingDiv.remove();
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'assistant-turn';
    if (!res.ok) {
      assistantDiv.textContent = `Error: ${data.error || data.detail || res.status}`;
    } else {
      assistantDiv.innerHTML = marked.parse(data.response);
      if (!currentConversationId) {
        currentConversationId = data.conversation_id;
        updateMeta(goal, userId, modeVal, data.conversation_id);
        document.getElementById('new-conv-form').style.display = 'none';
        refreshConversationList();
      }
    }
    history.appendChild(assistantDiv);
    history.scrollTop = history.scrollHeight;
  } catch (err) {
    loadingDiv.remove();
    const errDiv = document.createElement('div');
    errDiv.className = 'assistant-turn';
    errDiv.textContent = `Network error: ${err.message}`;
    history.appendChild(errDiv);
  } finally {
    btn.disabled = false;
    btn.removeAttribute('aria-busy');
  }
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
    const roots = data.roots;
    if (!Array.isArray(roots) || roots.length === 0) {
      tree.textContent = 'No roots found.';
      return;
    }
    roots.forEach(root => {
      renderEntry(tree, { name: root, type: 'directory' }, '');
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
    if (!name) { alert('Enter a name.'); return; }

    const parentPath = currentDirPath || '';
    const fullPath = parentPath ? parentPath + '/' + name : name;
    const btn = document.getElementById('new-file-create');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const res = await fetch('/files/' + encodePathSegments(fullPath), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: '' }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(`Create failed: ${data.error || data.detail || res.status}`);
      } else {
        nameInput.value = '';
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

  // New folder
  document.getElementById('new-folder-create').addEventListener('click', async () => {
    const nameInput = document.getElementById('new-file-name');
    const name = nameInput.value.trim();
    if (!name) { alert('Enter a name.'); return; }

    const parentPath = currentDirPath || '';
    const fullPath = parentPath ? parentPath + '/' + name : name;
    const btn = document.getElementById('new-folder-create');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    try {
      const res = await fetch('/files/' + encodePathSegments(fullPath), {
        method: 'POST',
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(`Create failed: ${data.error || data.detail || res.status}`);
      } else {
        nameInput.value = '';
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
  initGoalsTab();
  initFilesTab();
  initAdminTab();
  loadGoals();
});
