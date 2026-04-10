# Task 00010 — Product validation: trace every deliverable to a concrete artifact

## Agent
product-manager

## Goal
Verify that every deliverable listed in `project.md` exists and is correctly configured.
This is a read-only audit task — make only minimal fixes if a deliverable is missing or
misconfigured; do not add features.

## Prerequisites
- All prior tasks (00001–00009) must be complete

## Checklist

For each item below, verify the artifact exists and is correctly configured.

### Deliverable 1: `frontend/index.html`

```bash
test -f frontend/index.html && echo "EXISTS"
```

Open and confirm:
- Has five `<section id="tab-*">` elements: `tab-query`, `tab-conversation`, `tab-collection`, `tab-files`, `tab-admin`
- Has five elements with `data-tab` attributes
- Has one `<link>` to Pico.css CDN
- Has `<script src="app.js">` or `<script src="app.js" defer>`

### Deliverable 2: `frontend/app.js`

```bash
test -f frontend/app.js && echo "EXISTS"
```

Confirm:
- No `import React`, `import Vue`, `import Angular`, or similar framework imports
- Contains `fetch('/query'` or `fetch("/query"`
- Contains `fetch('/conversation'` or similar
- Contains `fetch('/collection/start'`
- Contains `fetch('/files'`
- Contains `fetch('/config'`
- Contains `localStorage`
- Contains `aria-busy`

### Deliverable 3: `frontend/style.css`

```bash
test -f frontend/style.css && echo "EXISTS"
```

### Deliverable 4: FastAPI `StaticFiles` mount at `/ui`

```bash
grep "StaticFiles" src/corpus_council/api/app.py
grep '"/ui"' src/corpus_council/api/app.py
```

Both must match. The mount path must be `/ui`, not `/static` or any other path.

### Deliverable 5: `src/corpus_council/api/routers/files.py`

```bash
test -f src/corpus_council/api/routers/files.py && echo "EXISTS"
grep "include_router(files" src/corpus_council/api/app.py && echo "REGISTERED"
```

### Deliverable 6: `src/corpus_council/api/routers/admin.py`

```bash
test -f src/corpus_council/api/routers/admin.py && echo "EXISTS"
grep "include_router(admin" src/corpus_council/api/app.py && echo "REGISTERED"
```

### Deliverable 7: Conversation and collection routers registered

```bash
grep "include_router(conversation" src/corpus_council/api/app.py && echo "conversation REGISTERED"
grep "include_router(collection" src/corpus_council/api/app.py && echo "collection REGISTERED"
```

### Deliverable 8: Integration tests

```bash
test -f tests/integration/test_files_router.py && echo "files tests EXIST"
test -f tests/integration/test_admin_router.py && echo "admin tests EXIST"
test -f tests/integration/test_router_registration.py && echo "registration tests EXIST"
```

### Deliverable 9: All tests pass

```bash
pytest -m "not llm" tests/ -q --tb=short 2>&1 | tail -5
```

### Deliverable 10: No out-of-scope features

Confirm:
- No authentication endpoints (`/login`, `/auth`, `/token`) in any router
- No server restart endpoint (`/restart`, `/reload`)
- No JS build artifacts (`package.json`, `node_modules/`, `*.bundle.js`, `webpack.config.js`)

```bash
test ! -f frontend/package.json && echo "no package.json"
test ! -d frontend/node_modules && echo "no node_modules"
grep -rn "include_router" src/corpus_council/api/app.py
```

## If any deliverable is missing or misconfigured

Fix only the specific configuration issue (e.g., wrong mount path, missing `include_router`
call). Do not re-implement features. If a file is entirely missing, mark the task blocked
and identify which prior task should have created it.

## Final verification

```bash
pytest -m "not llm" tests/ && ruff check src/ && ruff format --check src/ && pyright src/
```

All four must exit 0.

## Save Command

```bash
test -f frontend/index.html && \
test -f frontend/app.js && \
test -f frontend/style.css && \
test -f src/corpus_council/api/routers/files.py && \
test -f src/corpus_council/api/routers/admin.py && \
grep -q "include_router(files" src/corpus_council/api/app.py && \
grep -q "include_router(admin" src/corpus_council/api/app.py && \
grep -q "include_router(conversation" src/corpus_council/api/app.py && \
grep -q "include_router(collection" src/corpus_council/api/app.py && \
grep -q '"/ui"' src/corpus_council/api/app.py && \
echo "ALL DELIVERABLES PRESENT"
```

Must print `ALL DELIVERABLES PRESENT` and exit 0.
