# Task 00001 — Implement `src/corpus_council/api/routers/files.py`

## Agent
programmer

## Goal
Create the file management router that exposes five managed directories via a REST API.
This is a net-new Python file; no existing source files are modified except `models.py`
(add the new Pydantic models).

## Context

### AppConfig field names (from `src/corpus_council/core/config.py`)
- `corpus_dir` — Path
- `council_dir` — Path
- `templates_dir` — Path
- `plans_dir` — Path
- `goals_dir` — Path

### Existing Pydantic model conventions (from `src/corpus_council/api/models.py`)
- `ConfigDict(extra="forbid")` on every model
- `from __future__ import annotations` at top of every file

### Existing router pattern (from `src/corpus_council/api/routers/query.py`)
- `router = APIRouter()` with no prefix — paths are spelled out in each decorator
- `from corpus_council.api.app import config` inside the route handler (not at module level)
  to avoid circular imports

## Deliverables

### 1. Add Pydantic models to `src/corpus_council/api/models.py`

Append after the last existing model:

```python
from typing import Literal  # already imported at top

class FileEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: Literal["file", "directory"]
    size: int | None  # None for directories

class DirectoryListingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["directory"]
    entries: list[FileEntry]

class FileContentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["file"]
    content: str

class FileRootsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roots: list[str]

class FileWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str
```

### 2. Create `src/corpus_council/api/routers/files.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from corpus_council.api.models import (
    DirectoryListingResponse,
    FileContentResponse,
    FileEntry,
    FileRootsResponse,
    FileWriteRequest,
)

router = APIRouter()

# MANAGED_ROOTS is populated at first request (not import time) to avoid
# circular-import issues with app.py.  The helper _get_roots() is called
# inside every handler that needs them.
_MANAGED_ROOTS: dict[str, Path] | None = None


def _get_roots() -> dict[str, Path]:
    global _MANAGED_ROOTS
    if _MANAGED_ROOTS is None:
        from corpus_council.api.app import config
        _MANAGED_ROOTS = {
            "corpus": Path(config.corpus_dir).resolve(),
            "council": Path(config.council_dir).resolve(),
            "plans": Path(config.plans_dir).resolve(),
            "goals": Path(config.goals_dir).resolve(),
            "templates": Path(config.templates_dir).resolve(),
        }
    return _MANAGED_ROOTS


def _resolve_safe_path(root_key: str, rel_path: str) -> Path:
    """Resolve rel_path under the named root, rejecting traversal attempts."""
    # 1. Reject any '..' segment in the raw path string
    if ".." in rel_path.split("/"):
        raise HTTPException(status_code=400, detail="Path traversal not allowed")
    # 2. Validate root key
    roots = _get_roots()
    if root_key not in roots:
        raise HTTPException(status_code=404, detail=f"Unknown root: {root_key!r}")
    # 3. Resolve and assert prefix containment
    root = roots[root_key]
    resolved = (root / rel_path).resolve()
    if not str(resolved).startswith(str(root)):
        raise HTTPException(status_code=400, detail="Path escapes managed root")
    return resolved


@router.get("/files", response_model=FileRootsResponse)
async def list_roots() -> FileRootsResponse:
    """GET /files — return the names of the five managed root directories."""
    return FileRootsResponse(roots=list(_get_roots().keys()))


@router.get(
    "/files/{path:path}",
    response_model=Union[DirectoryListingResponse, FileContentResponse],
)
async def get_file_or_directory(
    path: str,
) -> DirectoryListingResponse | FileContentResponse:
    """GET /files/{path} — list a directory or return a file's text content."""
    # Split off the root key (first segment)
    parts = path.split("/", 1)
    root_key = parts[0]
    rel_path = parts[1] if len(parts) > 1 else ""

    if rel_path:
        resolved = _resolve_safe_path(root_key, rel_path)
    else:
        roots = _get_roots()
        if root_key not in roots:
            raise HTTPException(status_code=404, detail=f"Unknown root: {root_key!r}")
        resolved = roots[root_key]

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if resolved.is_dir():
        entries: list[FileEntry] = sorted(
            [
                FileEntry(
                    name=child.name,
                    type="directory" if child.is_dir() else "file",
                    size=None if child.is_dir() else child.stat().st_size,
                )
                for child in resolved.iterdir()
            ],
            key=lambda e: (e.type == "file", e.name.lower()),
        )
        return DirectoryListingResponse(type="directory", entries=entries)

    try:
        content = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read file") from exc
    return FileContentResponse(type="file", content=content)


@router.post("/files/{path:path}", status_code=201)
async def create_file(path: str, body: FileWriteRequest) -> None:
    """POST /files/{path} — create a new file; 409 if it already exists."""
    parts = path.split("/", 1)
    root_key = parts[0]
    rel_path = parts[1] if len(parts) > 1 else ""

    if not rel_path:
        raise HTTPException(status_code=400, detail="Cannot create a root directory")

    resolved = _resolve_safe_path(root_key, rel_path)

    if resolved.exists():
        raise HTTPException(status_code=409, detail="File already exists")

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(body.content, encoding="utf-8")


@router.put("/files/{path:path}", status_code=200)
async def update_file(path: str, body: FileWriteRequest) -> None:
    """PUT /files/{path} — overwrite an existing file's content."""
    parts = path.split("/", 1)
    root_key = parts[0]
    rel_path = parts[1] if len(parts) > 1 else ""

    if not rel_path:
        raise HTTPException(status_code=400, detail="Cannot overwrite a root directory")

    resolved = _resolve_safe_path(root_key, rel_path)

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is a directory")

    resolved.write_text(body.content, encoding="utf-8")


@router.delete("/files/{path:path}", status_code=204, response_class=Response)
async def delete_file(path: str) -> Response:
    """DELETE /files/{path} — delete a file; 204 on success."""
    parts = path.split("/", 1)
    root_key = parts[0]
    rel_path = parts[1] if len(parts) > 1 else ""

    if not rel_path:
        raise HTTPException(status_code=400, detail="Cannot delete a root directory")

    resolved = _resolve_safe_path(root_key, rel_path)

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is a directory")

    resolved.unlink()
    return Response(status_code=204)


__all__ = ["router"]
```

## Implementation Notes

- `_MANAGED_ROOTS` is lazily populated inside `_get_roots()` to avoid the circular import
  that would occur if `config` were accessed at module load time (before `app.py` finishes).
  **Important**: integration tests must patch `corpus_council.api.routers.files._MANAGED_ROOTS`
  directly (not `_get_roots`) so the patch takes effect before the first request.
- Directories are sorted: directories first, then files, each group case-insensitively by name.
- `size` is `None` for directory entries.
- All error responses flow through FastAPI exception handlers; no bare `except` blocks are used.

## Verification

```bash
ruff check src/
ruff format --check src/
pyright src/
```

All three must exit 0.

## Save Command

```bash
uv run python -c "from corpus_council.api.routers.files import router; print('import ok')"
```

Must print `import ok` and exit 0.
