from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from corpus_council.api.models import (
    DirectoryListingResponse,
    FileContentResponse,
    FileEntry,
    FileRootsResponse,
    FileWriteRequest,
)

router = APIRouter()


def _get_roots() -> dict[str, Path]:
    """Return managed root directories from config (lazy to avoid circular import)."""
    from corpus_council.api.app import config

    return {
        "corpus": config.corpus_dir.resolve(),
        "council": config.council_dir.resolve(),
        "templates": config.templates_dir.resolve(),
        "plans": config.plans_dir.resolve(),
        "goals": config.goals_dir.resolve(),
    }


def _resolve_safe_path(root_name: str, rel_path: str) -> Path:
    """Resolve rel_path under the named root, rejecting traversal attempts.

    Three-layer check:
    1. Reject any path containing '..' segments.
    2. Verify root_name is a known managed root.
    3. Verify resolved path is strictly under the root.

    Raises:
        HTTPException 400: on path traversal or invalid root.
        HTTPException 404: root directory itself does not exist.
    """
    # Reject '..' segments before any Path resolution to prevent traversal attacks.
    if ".." in rel_path.split("/"):
        raise HTTPException(
            status_code=400,
            detail="Path traversal with '..' is not allowed",
        )

    # Layer 2: verify root_name is known
    roots = _get_roots()
    if root_name not in roots:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown root {root_name!r}. Must be one of: {sorted(roots)}",
        )

    root = roots[root_name]

    # Layer 3: verify resolved path is under root
    candidate = (root / rel_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Path resolves outside the managed root directory",
        ) from exc

    return candidate


@router.get("/files", response_model=FileRootsResponse)
async def get_file_roots() -> FileRootsResponse:
    """GET /files — list the names of all managed root directories."""
    roots = _get_roots()
    return FileRootsResponse(roots=sorted(roots.keys()))


@router.get(
    "/files/{root}/{path:path}",
    response_model=DirectoryListingResponse | FileContentResponse,
)
async def get_file(
    root: str, path: str
) -> DirectoryListingResponse | FileContentResponse:
    """GET /files/{root}/{path} — read a file or list a directory."""
    resolved = _resolve_safe_path(root, path)

    if not resolved.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path!r}")

    if resolved.is_dir():
        entries: list[FileEntry] = []
        for child in sorted(resolved.iterdir()):
            entry_type: str
            size: int | None
            if child.is_dir():
                entry_type = "directory"
                size = None
            else:
                entry_type = "file"
                size = child.stat().st_size
            entries.append(
                FileEntry(name=child.name, type=entry_type, size=size)  # type: ignore[arg-type]
            )
        return DirectoryListingResponse(type="directory", entries=entries)

    # It's a file
    content = resolved.read_text(encoding="utf-8")
    return FileContentResponse(type="file", content=content)


@router.put("/files/{root}/{path:path}", response_model=FileContentResponse)
async def put_file(root: str, path: str, body: FileWriteRequest) -> FileContentResponse:
    """PUT /files/{root}/{path} — create or overwrite a file."""
    resolved = _resolve_safe_path(root, path)

    if resolved.is_dir():
        raise HTTPException(
            status_code=400, detail=f"Path {path!r} is a directory, not a file"
        )

    # Create parent directories if needed
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(body.content, encoding="utf-8")
    return FileContentResponse(type="file", content=body.content)


@router.post("/files/{root}/{path:path}")
async def create_directory(root: str, path: str) -> dict[str, str]:
    """POST /files/{root}/{path} — create a directory."""
    resolved = _resolve_safe_path(root, path)

    if resolved.exists() and not resolved.is_dir():
        raise HTTPException(
            status_code=400, detail=f"Path {path!r} already exists as a file"
        )

    resolved.mkdir(parents=True, exist_ok=True)
    return {"created": path, "type": "directory"}


@router.delete("/files/{root}/{path:path}")
async def delete_file(root: str, path: str) -> dict[str, str]:
    """DELETE /files/{root}/{path} — delete a file."""
    resolved = _resolve_safe_path(root, path)

    if not resolved.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path!r}")

    if resolved.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path {path!r} is a directory; only files can be deleted",
        )

    resolved.unlink()
    return {"deleted": path}


__all__ = ["router"]
