from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]

from corpus_council.core.config import AppConfig

_REQUIRED_FIELDS: list[str] = [
    "name",
    "persona",
    "primary_lens",
    "position",
    "role_type",
    "escalation_rule",
]


@dataclass
class CouncilMember:
    name: str
    persona: str
    primary_lens: str
    position: int
    role_type: str
    escalation_rule: str
    body: str
    source_file: str


def _parse_member(path: Path, council_dir: Path) -> CouncilMember:
    """Parse a single council member markdown file.

    Raises:
        ValueError: if a required field is missing or position cannot be cast to int.
    """
    post = frontmatter.load(str(path))
    metadata: dict[str, Any] = dict(post.metadata)

    for field in _REQUIRED_FIELDS:
        if field not in metadata:
            raise ValueError(f"Council file {path} missing required field: {field}")

    try:
        position = int(metadata["position"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Council file {path} field 'position' cannot be cast to int: "
            f"{metadata['position']!r}"
        ) from exc

    name = metadata["name"]
    if not isinstance(name, str):
        raise ValueError(
            f"Council file {path} field 'name' must be a string, "
            f"got {type(name).__name__!r}"
        )

    persona = metadata["persona"]
    if not isinstance(persona, str):
        raise ValueError(
            f"Council file {path} field 'persona' must be a string, "
            f"got {type(persona).__name__!r}"
        )

    primary_lens = metadata["primary_lens"]
    if not isinstance(primary_lens, str):
        raise ValueError(
            f"Council file {path} field 'primary_lens' must be a string, "
            f"got {type(primary_lens).__name__!r}"
        )

    role_type = metadata["role_type"]
    if not isinstance(role_type, str):
        raise ValueError(
            f"Council file {path} field 'role_type' must be a string, "
            f"got {type(role_type).__name__!r}"
        )

    escalation_rule = metadata["escalation_rule"]
    if not isinstance(escalation_rule, str):
        raise ValueError(
            f"Council file {path} field 'escalation_rule' must be a string, "
            f"got {type(escalation_rule).__name__!r}"
        )

    body: str = post.content
    source_file = str(path.relative_to(council_dir))

    return CouncilMember(
        name=name,
        persona=persona,
        primary_lens=primary_lens,
        position=position,
        role_type=role_type,
        escalation_rule=escalation_rule,
        body=body,
        source_file=source_file,
    )


def load_council(config: AppConfig) -> list[CouncilMember]:
    """Load all council members from the council directory.

    Reads all .md files in config.council_dir, parses YAML front matter,
    validates required fields, and returns members sorted by position ascending.

    Raises:
        ValueError: if any council file is missing required fields or has invalid data.
    """
    council_dir = config.council_dir
    members: list[CouncilMember] = []

    for md_path in sorted(council_dir.glob("*.md")):
        member = _parse_member(md_path, council_dir)
        members.append(member)

    members.sort(key=lambda m: m.position)
    return members


__all__ = ["CouncilMember", "load_council"]
