from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
from typing import Any


class FileStore:
    """Single gateway for all user/session file-based persistence.

    Data is sharded into a 2-level directory structure:
        {base}/users/{user_id[0:2]}/{user_id[2:4]}/{user_id}/
    """

    def __init__(self, base: Path) -> None:
        self.base = base

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------

    def user_dir(self, user_id: str) -> Path:
        if len(user_id) < 4:
            raise ValueError(f"user_id must be at least 4 characters, got: {user_id!r}")
        return self.base / "users" / user_id[0:2] / user_id[2:4] / user_id

    # ------------------------------------------------------------------
    # Core I/O primitives
    # ------------------------------------------------------------------

    def append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        tmp.replace(path)  # atomic rename

    def read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with open(path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)  # type: ignore[no-any-return]
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with open(path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return records

    # ------------------------------------------------------------------
    # Convenience path builders — chat
    # ------------------------------------------------------------------

    def chat_messages_path(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "chat" / "messages.jsonl"

    def chat_context_path(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "chat" / "context.json"

    # ------------------------------------------------------------------
    # Convenience path builders — goal chat
    # ------------------------------------------------------------------

    def goal_messages_path(self, user_id: str, goal: str, conversation_id: str) -> Path:
        return (
            self.user_dir(user_id) / "goals" / goal / conversation_id / "messages.jsonl"
        )

    def goal_context_path(self, user_id: str, goal: str, conversation_id: str) -> Path:
        return (
            self.user_dir(user_id) / "goals" / goal / conversation_id / "context.json"
        )

    # ------------------------------------------------------------------
    # Convenience path builders — collection
    # ------------------------------------------------------------------

    def collection_dir(self, user_id: str, session_id: str) -> Path:
        return self.user_dir(user_id) / "collection" / session_id

    def collection_session_path(self, user_id: str, session_id: str) -> Path:
        return self.collection_dir(user_id, session_id) / "session.json"

    def collection_messages_path(self, user_id: str, session_id: str) -> Path:
        return self.collection_dir(user_id, session_id) / "messages.jsonl"

    def collection_collected_path(self, user_id: str, session_id: str) -> Path:
        return self.collection_dir(user_id, session_id) / "collected.json"

    def collection_context_path(self, user_id: str, session_id: str) -> Path:
        return self.collection_dir(user_id, session_id) / "context.json"


__all__ = ["FileStore"]
