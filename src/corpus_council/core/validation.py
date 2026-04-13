from __future__ import annotations

import re
from pathlib import Path

_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{4,128}$")


def validate_id(value: str, name: str) -> str:
    if not _SAFE_ID.match(value):
        raise ValueError(
            f"{name} must be 4-128 alphanumeric/dash/underscore"
            f" characters, got: {value!r}"
        )
    return value


def validate_path_containment(candidate: Path, parent: Path, label: str) -> Path:
    resolved = candidate.resolve()
    resolved_parent = parent.resolve()
    if not str(resolved).startswith(str(resolved_parent)):
        raise ValueError(f"{label} resolves outside expected directory: {resolved}")
    return resolved


__all__ = ["validate_id", "validate_path_containment"]
