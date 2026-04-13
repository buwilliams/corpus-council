from __future__ import annotations

import threading
from pathlib import Path

import pytest

from corpus_council.core.store import FileStore

# ---------------------------------------------------------------------------
# Tests: user_dir sharding
# ---------------------------------------------------------------------------


def test_user_dir_correct_sharding(tmp_path: Path) -> None:
    """user_id 'abc123ef' should produce a path ending with ab/c1/abc123ef."""
    users_dir = tmp_path / "users"
    store = FileStore(users_dir)
    user_id = "abc123ef"

    result = store.user_dir(user_id)

    assert result == users_dir / "ab" / "c1" / "abc123ef"


def test_user_dir_raises_for_short_id(tmp_path: Path) -> None:
    """user_id 'ab' (len < 4) should raise ValueError."""
    store = FileStore(tmp_path / "users")

    with pytest.raises(ValueError):
        store.user_dir("ab")


# ---------------------------------------------------------------------------
# Tests: append_jsonl
# ---------------------------------------------------------------------------


def test_append_jsonl_writes_record(tmp_path: Path) -> None:
    """Append a single record; read it back and assert it equals the original."""
    store = FileStore(tmp_path)
    path = tmp_path / "records.jsonl"
    record = {"key": "value", "number": 42}

    store.append_jsonl(path, record)
    result = store.read_jsonl(path)

    assert result == [record]


def test_append_jsonl_multiple_records(tmp_path: Path) -> None:
    """Append 3 records; assert all 3 are returned by read_jsonl."""
    store = FileStore(tmp_path)
    path = tmp_path / "multi.jsonl"
    records = [{"index": i, "data": f"item{i}"} for i in range(3)]

    for rec in records:
        store.append_jsonl(path, rec)

    result = store.read_jsonl(path)

    assert result == records


# ---------------------------------------------------------------------------
# Tests: write_json / read_json
# ---------------------------------------------------------------------------


def test_write_json_and_read_json_roundtrip(tmp_path: Path) -> None:
    """Write a dict with write_json; read it back with read_json and assert equal."""
    store = FileStore(tmp_path)
    path = tmp_path / "data.json"
    data = {"name": "Alice", "score": 99, "tags": ["a", "b"]}

    store.write_json(path, data)
    result = store.read_json(path)

    assert result == data


def test_read_json_returns_empty_dict_for_missing_file(tmp_path: Path) -> None:
    """read_json on a nonexistent path should return an empty dict."""
    store = FileStore(tmp_path)
    path = tmp_path / "does_not_exist.json"

    result = store.read_json(path)

    assert result == {}


def test_read_jsonl_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    """read_jsonl on a nonexistent path should return an empty list."""
    store = FileStore(tmp_path)
    path = tmp_path / "does_not_exist.jsonl"

    result = store.read_jsonl(path)

    assert result == []


# ---------------------------------------------------------------------------
# Tests: concurrent writes
# ---------------------------------------------------------------------------


def test_concurrent_appends_do_not_corrupt_data(tmp_path: Path) -> None:
    """10 threads appending simultaneously should produce exactly 10 records."""
    store = FileStore(tmp_path)
    path = tmp_path / "concurrent.jsonl"
    num_threads = 10
    barrier = threading.Barrier(num_threads)

    def append_one(index: int) -> None:
        barrier.wait()  # ensure all threads start at the same time
        store.append_jsonl(path, {"thread": index})

    threads = [
        threading.Thread(target=append_one, args=(i,)) for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    records = store.read_jsonl(path)
    assert len(records) == num_threads
    # Verify all thread indices are present (no records lost or duplicated)
    indices = sorted(r["thread"] for r in records)
    assert indices == list(range(num_threads))


# ---------------------------------------------------------------------------
# Tests: atomicity
# ---------------------------------------------------------------------------


def test_write_json_is_atomic(tmp_path: Path) -> None:
    """write_json leaves no partial data: read after write returns the full dict."""
    store = FileStore(tmp_path)
    path = tmp_path / "atomic.json"
    # Write a reasonably large dict to make partial writes more likely to surface
    data = {f"key_{i}": f"value_{i}" * 20 for i in range(200)}

    store.write_json(path, data)
    result = store.read_json(path)

    assert result == data


# ---------------------------------------------------------------------------
# Tests: goal path helpers
# ---------------------------------------------------------------------------


def test_goal_messages_path_correct_structure(tmp_path: Path) -> None:
    """goal_messages_path should produce the expected sharded path ending."""
    store = FileStore(tmp_path / "users")

    result = store.goal_messages_path("abc123ef", "my-goal", "conv-uuid")

    assert str(result).endswith(
        "users/ab/c1/abc123ef/goals/my-goal/conv-uuid/messages.jsonl"
    )


def test_goal_context_path_correct_structure(tmp_path: Path) -> None:
    """goal_context_path should produce the expected sharded path ending."""
    store = FileStore(tmp_path / "users")

    result = store.goal_context_path("abc123ef", "my-goal", "conv-uuid")

    assert str(result).endswith(
        "users/ab/c1/abc123ef/goals/my-goal/conv-uuid/context.json"
    )
