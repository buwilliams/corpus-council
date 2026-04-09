from __future__ import annotations

import json
from pathlib import Path

import pytest

from corpus_council.core.goals import (
    CouncilMemberRef,
    GoalConfig,
    load_goal,
    parse_goal_file,
    process_goals,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOAL_FRONT_MATTER = """\
---
desired_outcome: "Run intake"
corpus_path: "corpus"
council:
  - persona_file: "advisor.md"
    authority_tier: 1
  - persona_file: "analyst.md"
    authority_tier: 2
---
Body text.
"""


def _write_persona(personas_dir: Path, filename: str) -> None:
    """Create a minimal persona file inside personas_dir."""
    (personas_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")


def _write_goal(goals_dir: Path, name: str, content: str) -> Path:
    """Write a goal markdown file and return its path."""
    path = goals_dir / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# parse_goal_file tests
# ---------------------------------------------------------------------------


def test_parse_goal_file_happy_path(tmp_path: Path) -> None:
    """parse_goal_file returns a correct GoalConfig for a well-formed goal file."""
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    _write_persona(personas_dir, "advisor.md")
    _write_persona(personas_dir, "analyst.md")

    goal_path = _write_goal(tmp_path, "my-goal", _GOAL_FRONT_MATTER)

    config = parse_goal_file(goal_path, personas_dir)

    assert isinstance(config, GoalConfig)
    assert config.name == "my-goal"
    assert config.desired_outcome == "Run intake"
    assert config.corpus_path == "corpus"
    assert len(config.council) == 2
    assert config.council[0] == CouncilMemberRef(
        persona_file="advisor.md", authority_tier=1
    )
    assert config.council[1] == CouncilMemberRef(
        persona_file="analyst.md", authority_tier=2
    )


def test_parse_goal_file_raises_on_missing_persona(tmp_path: Path) -> None:
    """parse_goal_file raises ValueError when a council persona_file does not exist."""
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    # Only create advisor.md; analyst.md is intentionally absent
    _write_persona(personas_dir, "advisor.md")

    goal_path = _write_goal(tmp_path, "bad-goal", _GOAL_FRONT_MATTER)

    with pytest.raises(ValueError, match="persona_file does not exist"):
        parse_goal_file(goal_path, personas_dir)


def test_parse_goal_file_raises_on_path_traversal(tmp_path: Path) -> None:
    """parse_goal_file raises ValueError when a persona_file uses path traversal."""
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()

    traversal_content = """\
---
desired_outcome: "Attack"
corpus_path: "corpus"
council:
  - persona_file: "../../etc/passwd"
    authority_tier: 1
---
"""
    goal_path = _write_goal(tmp_path, "traversal-goal", traversal_content)

    with pytest.raises(ValueError, match="persona_file"):
        parse_goal_file(goal_path, personas_dir)


def test_parse_goal_file_raises_on_missing_desired_outcome(tmp_path: Path) -> None:
    """parse_goal_file raises ValueError when the 'desired_outcome' field is absent."""
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    _write_persona(personas_dir, "advisor.md")

    content = """\
---
corpus_path: "corpus"
council:
  - persona_file: "advisor.md"
    authority_tier: 1
---
"""
    goal_path = _write_goal(tmp_path, "no-outcome", content)

    with pytest.raises(ValueError, match="desired_outcome"):
        parse_goal_file(goal_path, personas_dir)


# ---------------------------------------------------------------------------
# process_goals tests
# ---------------------------------------------------------------------------


def test_process_goals_writes_all_goals(tmp_path: Path) -> None:
    """process_goals reads every .md file in goals_dir and writes them to manifest."""
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    manifest_path = tmp_path / "goals_manifest.json"

    _write_persona(personas_dir, "advisor.md")
    _write_persona(personas_dir, "analyst.md")

    _write_goal(goals_dir, "alpha", _GOAL_FRONT_MATTER)
    _write_goal(goals_dir, "beta", _GOAL_FRONT_MATTER)

    results = process_goals(goals_dir, personas_dir, manifest_path)

    assert len(results) == 2
    names = {g.name for g in results}
    assert names == {"alpha", "beta"}
    assert manifest_path.exists()

    with open(manifest_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    assert len(data) == 2


def test_process_goals_idempotent(tmp_path: Path) -> None:
    """process_goals produces byte-for-byte identical manifest on repeated calls."""
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    manifest_path = tmp_path / "goals_manifest.json"

    _write_persona(personas_dir, "advisor.md")
    _write_persona(personas_dir, "analyst.md")
    _write_goal(goals_dir, "my-goal", _GOAL_FRONT_MATTER)

    process_goals(goals_dir, personas_dir, manifest_path)
    first_bytes = manifest_path.read_bytes()

    process_goals(goals_dir, personas_dir, manifest_path)
    second_bytes = manifest_path.read_bytes()

    assert first_bytes == second_bytes


def test_process_goals_empty_dir_writes_empty_manifest(tmp_path: Path) -> None:
    """process_goals writes an empty JSON array when goals_dir contains no .md files."""
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    manifest_path = tmp_path / "goals_manifest.json"

    results = process_goals(goals_dir, personas_dir, manifest_path)

    assert results == []
    assert manifest_path.exists()

    with open(manifest_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data == []


# ---------------------------------------------------------------------------
# load_goal tests
# ---------------------------------------------------------------------------


def _make_manifest(manifest_path: Path, goals: list[GoalConfig]) -> None:
    """Write a goals manifest JSON file from a list of GoalConfig objects."""
    import dataclasses

    entries = [
        {
            "name": g.name,
            "desired_outcome": g.desired_outcome,
            "corpus_path": g.corpus_path,
            "council": [dataclasses.asdict(ref) for ref in g.council],
        }
        for g in goals
    ]
    manifest_path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_load_goal_returns_correct_config(tmp_path: Path) -> None:
    """load_goal returns the GoalConfig that matches the requested name."""
    manifest_path = tmp_path / "goals_manifest.json"
    expected = GoalConfig(
        name="intake",
        desired_outcome="Run intake",
        council=[
            CouncilMemberRef(persona_file="advisor.md", authority_tier=1),
        ],
        corpus_path="corpus",
    )
    _make_manifest(manifest_path, [expected])

    result = load_goal("intake", manifest_path)

    assert result.name == "intake"
    assert result.desired_outcome == "Run intake"
    assert result.corpus_path == "corpus"
    assert len(result.council) == 1
    assert result.council[0].persona_file == "advisor.md"
    assert result.council[0].authority_tier == 1


def test_load_goal_raises_on_missing_name(tmp_path: Path) -> None:
    """load_goal raises ValueError when the requested name is not in the manifest."""
    manifest_path = tmp_path / "goals_manifest.json"
    existing = GoalConfig(
        name="intake",
        desired_outcome="Run intake",
        council=[],
        corpus_path="corpus",
    )
    _make_manifest(manifest_path, [existing])

    with pytest.raises(ValueError, match="Goal not found in manifest"):
        load_goal("nonexistent-goal", manifest_path)


def test_load_goal_raises_on_missing_manifest(tmp_path: Path) -> None:
    """load_goal raises FileNotFoundError when the manifest file does not exist."""
    manifest_path = tmp_path / "no_manifest.json"

    with pytest.raises(FileNotFoundError, match="Goals manifest not found"):
        load_goal("any-goal", manifest_path)
