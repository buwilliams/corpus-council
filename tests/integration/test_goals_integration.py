from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_GOALS_DIR = PROJECT_ROOT / "goals"


def _write_persona_files(council_dir: Path) -> None:
    """Write coach.md and analyst.md to council_dir with valid front matter."""
    council_dir.mkdir(parents=True, exist_ok=True)

    (council_dir / "coach.md").write_text(
        "---\n"
        "name: Coach\n"
        "persona: Coach\n"
        "primary_lens: coaching\n"
        "position: 1\n"
        "role_type: synthesizer\n"
        "escalation_rule: Halt if off-topic\n"
        "---\n"
        "Coach body.\n",
        encoding="utf-8",
    )

    (council_dir / "analyst.md").write_text(
        "---\n"
        "name: Analyst\n"
        "persona: Analyst\n"
        "primary_lens: analysis\n"
        "position: 2\n"
        "role_type: domain_specialist\n"
        "escalation_rule: Halt if out of scope\n"
        "---\n"
        "Analyst body.\n",
        encoding="utf-8",
    )


def _write_config(tmp_path: Path) -> Path:
    """Write a config.yaml to tmp_path and return its path.

    data_dir is set to tmp_path so derived paths (corpus, council, goals, etc.)
    resolve to the directories created by the fixture.
    """
    config_data = {
        "llm": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
        },
        "embedding": {
            "provider": "sentence-transformers",
            "model": "all-MiniLM-L6-v2",
        },
        "data_dir": str(tmp_path),
        "chunking": {"max_size": 512},
        "retrieval": {"top_k": 3},
        "chroma_collection": "test_corpus",
        "deliberation_mode": "parallel",
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config_data), encoding="utf-8")
    return config_path


@pytest.fixture()
def goals_workspace(tmp_path: Path) -> Path:
    """
    Set up a workspace with:
    - Real goal files (intake.md, create-plan.md) copied to tmp_path/goals/
    - Persona files (coach.md, analyst.md) written to tmp_path/council/
    - A config.yaml written to tmp_path/
    Returns tmp_path.
    """
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir(parents=True, exist_ok=True)

    # Copy real goal files into the workspace
    for goal_file in ("intake.md", "create-plan.md"):
        src = REAL_GOALS_DIR / goal_file
        if src.exists():
            shutil.copy2(src, goals_dir / goal_file)

    # Write persona files that the goal files reference
    council_dir = tmp_path / "council"
    _write_persona_files(council_dir)

    # Create required directories
    for d in ("data", "corpus", "plans"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Write config.yaml
    _write_config(tmp_path)

    return tmp_path


def test_goals_process_command_exits_zero(goals_workspace: Path) -> None:
    """Run 'corpus-council goals process' and assert exit 0 and manifest exists."""
    result = subprocess.run(
        ["uv", "run", "corpus-council", "goals", "process"],
        cwd=str(goals_workspace),
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 0, (
        f"goals process exited {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    manifest_path = goals_workspace / "goals_manifest.json"
    assert manifest_path.exists(), "goals_manifest.json was not created"
