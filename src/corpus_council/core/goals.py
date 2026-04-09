"""Goals model for corpus-council.

A goal is a markdown file that declares a desired outcome, a list of council
members (with authority tiers), and a corpus scope. Goals are pre-processed
offline via ``corpus-council goals process`` into ``goals_manifest.json``.
At runtime, ``--goal <name>`` loads the named goal from the manifest.

Goal file format (YAML front matter in a ``.md`` file)::

    ---
    desired_outcome: "Human-readable description of the desired outcome."
    corpus_path: "corpus"
    council:
      - persona_file: "coach.md"   # relative to personas_dir
        authority_tier: 1          # 1 = highest authority
      - persona_file: "analyst.md"
        authority_tier: 2
    ---
    Optional body text with additional context for the council.

See docs/goal-authoring-guide.md for the full authoring guide.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]

from corpus_council.core.validation import validate_path_containment

__all__ = [
    "CouncilMemberRef",
    "GoalConfig",
    "parse_goal_file",
    "process_goals",
    "load_goal",
]


@dataclass
class CouncilMemberRef:
    persona_file: str
    authority_tier: int


@dataclass
class GoalConfig:
    name: str
    desired_outcome: str
    council: list[CouncilMemberRef]
    corpus_path: str


def _validate_persona_path(persona_file: str, personas_dir: Path) -> Path:
    """Resolve and validate that persona_file stays within personas_dir.

    Raises:
        ValueError: if the resolved path escapes personas_dir or does not exist.
    """
    resolved = validate_path_containment(
        personas_dir / persona_file, personas_dir, "persona_file"
    )
    if not resolved.exists():
        raise ValueError(f"persona_file does not exist: {resolved}")
    return resolved


def parse_goal_file(path: Path, personas_dir: Path) -> GoalConfig:
    """Parse a goal markdown file with YAML front matter.

    Raises:
        ValueError: if required fields are missing, invalid, or persona paths escape
                    the personas directory.
        FileNotFoundError: if the goal file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Goal file not found: {path}")

    post = frontmatter.load(str(path))
    metadata: dict[str, Any] = dict(post.metadata)

    # Validate required fields
    for field in ("desired_outcome", "corpus_path", "council"):
        if field not in metadata:
            raise ValueError(f"Goal file {path} missing required field: {field!r}")

    desired_outcome = metadata["desired_outcome"]
    if not isinstance(desired_outcome, str):
        raise ValueError(
            f"Goal file {path} field 'desired_outcome' must be a string, "
            f"got {type(desired_outcome).__name__!r}"
        )

    corpus_path = metadata["corpus_path"]
    if not isinstance(corpus_path, str):
        raise ValueError(
            f"Goal file {path} field 'corpus_path' must be a string, "
            f"got {type(corpus_path).__name__!r}"
        )

    raw_council = metadata["council"]
    if not isinstance(raw_council, list):
        raise ValueError(
            f"Goal file {path} field 'council' must be a list, "
            f"got {type(raw_council).__name__!r}"
        )

    council: list[CouncilMemberRef] = []
    for i, entry in enumerate(raw_council):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Goal file {path} council entry {i} must be a mapping, "
                f"got {type(entry).__name__!r}"
            )
        if "persona_file" not in entry:
            raise ValueError(
                f"Goal file {path} council entry {i} missing 'persona_file'"
            )
        if "authority_tier" not in entry:
            raise ValueError(
                f"Goal file {path} council entry {i} missing 'authority_tier'"
            )

        pf = entry["persona_file"]
        if not isinstance(pf, str):
            raise ValueError(
                f"Goal file {path} council entry {i} 'persona_file' must be a string, "
                f"got {type(pf).__name__!r}"
            )

        at = entry["authority_tier"]
        try:
            at_int = int(at)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Goal file {path} council entry {i} 'authority_tier' cannot be cast "
                f"to int: {at!r}"
            ) from exc

        # Validate path containment for every persona reference
        _validate_persona_path(pf, personas_dir)

        council.append(CouncilMemberRef(persona_file=pf, authority_tier=at_int))

    name = path.stem
    return GoalConfig(
        name=name,
        desired_outcome=desired_outcome,
        council=council,
        corpus_path=corpus_path,
    )


def _goal_to_dict(goal: GoalConfig) -> dict[str, Any]:
    """Serialize a GoalConfig to a JSON-compatible dict."""
    return {
        "name": goal.name,
        "desired_outcome": goal.desired_outcome,
        "corpus_path": goal.corpus_path,
        "council": [asdict(ref) for ref in goal.council],
    }


def process_goals(
    goals_dir: Path, personas_dir: Path, manifest_path: Path
) -> list[GoalConfig]:
    """Read all .md files from goals_dir, validate them, and write goals_manifest.json.

    The manifest is written atomically via a .tmp rename and is byte-for-byte
    idempotent on repeated runs (sorted by name, sort_keys=True, indent=2).

    Raises:
        ValueError: if any goal file has invalid content or persona path traversal.
    """
    goals: list[GoalConfig] = []
    for md_path in sorted(goals_dir.glob("*.md")):
        goal = parse_goal_file(md_path, personas_dir)
        goals.append(goal)

    goals.sort(key=lambda g: g.name)

    manifest_data = [_goal_to_dict(g) for g in goals]

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest_data, fh, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(manifest_path)

    return goals


def load_goal(name: str, manifest_path: Path) -> GoalConfig:
    """Load a single goal by name from the goals manifest.

    Raises:
        FileNotFoundError: if the manifest file does not exist.
        ValueError: if the named goal is not found in the manifest.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Goals manifest not found: {manifest_path}")

    with open(manifest_path, encoding="utf-8") as fh:
        raw: Any = json.load(fh)

    if not isinstance(raw, list):
        raise ValueError(
            f"Goals manifest must contain a JSON array, got {type(raw).__name__!r}"
        )

    for entry in raw:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") == name:
            council: list[CouncilMemberRef] = []
            for ref in entry.get("council", []):
                council.append(
                    CouncilMemberRef(
                        persona_file=str(ref["persona_file"]),
                        authority_tier=int(ref["authority_tier"]),
                    )
                )
            return GoalConfig(
                name=str(entry["name"]),
                desired_outcome=str(entry["desired_outcome"]),
                council=council,
                corpus_path=str(entry["corpus_path"]),
            )

    raise ValueError(f"Goal not found in manifest: {name!r}")
