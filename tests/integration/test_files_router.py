from __future__ import annotations

from pathlib import Path

import httpx
import pytest

import corpus_council.api.app as app_module
import corpus_council.api.routers.files as files_module
from corpus_council.core.config import AppConfig
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def managed_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Create three tmp subdirectories and patch _get_roots to point at them."""
    roots: dict[str, Path] = {
        "corpus": tmp_path / "corpus",
        "council": tmp_path / "council",
        "goals": tmp_path / "goals",
    }
    for d in roots.values():
        d.mkdir(parents=True, exist_ok=True)
    resolved = {k: v.resolve() for k, v in roots.items()}
    monkeypatch.setattr(files_module, "_get_roots", lambda: resolved)
    return resolved


@pytest.fixture
async def client(
    managed_roots: dict[str, Path],
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    monkeypatch.setattr(app_module, "config", test_config)
    monkeypatch.setattr(app_module, "store", FileStore(test_config.data_dir))
    monkeypatch.setattr(app_module, "llm", LLMClient(test_config))

    from corpus_council.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_list_roots(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files returns 200 with all five root names."""
    response = await client.get("/files")
    assert response.status_code == 200
    data = response.json()
    assert set(data["roots"]) == {"corpus", "council", "goals"}


async def test_list_directory(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files/corpus/ lists files in the corpus root."""
    (managed_roots["corpus"] / "doc.md").write_text("hello", encoding="utf-8")
    response = await client.get("/files/corpus/")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "directory"
    names = [e["name"] for e in data["entries"]]
    assert "doc.md" in names


async def test_list_directory_entry_fields(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """Directory entries have correct type and size fields."""
    (managed_roots["corpus"] / "file.txt").write_text("abc", encoding="utf-8")
    response = await client.get("/files/corpus/")
    data = response.json()
    file_entry = next(e for e in data["entries"] if e["name"] == "file.txt")
    assert file_entry["type"] == "file"
    assert file_entry["size"] == 3


async def test_read_file(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files/corpus/doc.md returns file content."""
    (managed_roots["corpus"] / "doc.md").write_text("# Hello\n", encoding="utf-8")
    response = await client.get("/files/corpus/doc.md")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "file"
    assert data["content"] == "# Hello\n"


async def test_read_nested_file(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files/corpus/sub/nested.md reads a file in a subdirectory."""
    sub = managed_roots["corpus"] / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("nested content", encoding="utf-8")
    response = await client.get("/files/corpus/sub/nested.md")
    assert response.status_code == 200
    assert response.json()["content"] == "nested content"


async def test_write_file(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """PUT /files/corpus/new.md creates a new file and returns 200."""
    response = await client.put(
        "/files/corpus/new.md", json={"content": "created content"}
    )
    assert response.status_code == 200
    assert (managed_roots["corpus"] / "new.md").read_text(
        encoding="utf-8"
    ) == "created content"


async def test_write_file_creates_parent_dirs(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """PUT /files/corpus/sub/dir/file.md creates intermediate directories."""
    response = await client.put(
        "/files/corpus/sub/dir/file.md", json={"content": "deep"}
    )
    assert response.status_code == 200
    assert (managed_roots["corpus"] / "sub" / "dir" / "file.md").exists()


async def test_write_file_overwrites_existing(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """PUT /files/corpus/doc.md overwrites an existing file."""
    (managed_roots["corpus"] / "doc.md").write_text("old", encoding="utf-8")
    response = await client.put("/files/corpus/doc.md", json={"content": "new content"})
    assert response.status_code == 200
    assert (managed_roots["corpus"] / "doc.md").read_text(
        encoding="utf-8"
    ) == "new content"


async def test_delete_file(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """DELETE /files/corpus/doc.md succeeds (2xx) and removes the file."""
    target = managed_roots["corpus"] / "doc.md"
    target.write_text("delete me", encoding="utf-8")
    response = await client.delete("/files/corpus/doc.md")
    assert response.status_code in {200, 204}
    assert not target.exists()


async def test_delete_file_not_found(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """DELETE /files/corpus/missing.md returns 404."""
    response = await client.delete("/files/corpus/missing.md")
    assert response.status_code == 404


async def test_path_traversal_rejected(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """Path traversal via URL-encoded '..' returns 400."""
    # Use percent-encoded '..' so the ASGI layer does not normalize the URL
    # before the router sees the path segments.
    response = await client.get("/files/corpus/%2E%2E/config.yaml")
    assert response.status_code == 400, (
        f"Expected 400 for traversal attempt, got {response.status_code}"
    )


async def test_path_outside_roots_rejected(
    client: httpx.AsyncClient, managed_roots: dict[str, Path], tmp_path: Path
) -> None:
    """A path that resolves outside the managed root returns 400 or 404."""
    # Create a symlink inside corpus that points outside
    link = managed_roots["corpus"] / "escape_link"
    link.symlink_to(tmp_path)
    response = await client.get("/files/corpus/escape_link")
    # Either the traversal check or the startswith check fires — either way not 200
    assert response.status_code in {400, 404}


async def test_unknown_root_rejected(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files/secrets/anything returns 4xx for unknown root."""
    response = await client.get("/files/secrets/anything")
    assert response.status_code in {400, 404}


async def test_read_nonexistent_file_returns_404(
    client: httpx.AsyncClient, managed_roots: dict[str, Path]
) -> None:
    """GET /files/corpus/missing.md returns 404."""
    response = await client.get("/files/corpus/missing.md")
    assert response.status_code == 404
