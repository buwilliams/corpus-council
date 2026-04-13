from __future__ import annotations

from pathlib import Path

import pytest

from corpus_council.core.config import AppConfig
from corpus_council.core.goals import process_goals
from corpus_council.core.store import FileStore


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """Write realistic corpus files to tmp_path/corpus."""
    d = tmp_path / "corpus"
    d.mkdir(parents=True, exist_ok=True)

    (d / "ai_progress.md").write_text(
        "# The Rapid Progress of Artificial Intelligence\n\n"
        "Artificial intelligence has transformed industries over the past decade. "
        "Machine learning models now outperform humans on image recognition tasks, "
        "and large language models can generate coherent text across many domains. "
        "Researchers push the boundaries of what is computationally feasible.\n\n"
        "Key advances include transformer architectures, reinforcement learning "
        "from human feedback, and multimodal models that process text and images.\n",
        encoding="utf-8",
    )

    (d / "nutrition_basics.md").write_text(
        "# Fundamentals of Human Nutrition\n\n"
        "A balanced diet provides macronutrients — carbohydrates, proteins, and "
        "fats — alongside essential micronutrients such as vitamins and minerals. "
        "Dietary fibre supports gut health and reduces chronic disease risk. "
        "Hydration matters; the body is approximately 60 percent water.\n\n"
        "Nutritionists recommend whole foods rather than processed alternatives, "
        "which often contain excessive sodium and added sugars.\n",
        encoding="utf-8",
    )

    (d / "education_reform.md").write_text(
        "# Rethinking Education for the 21st Century\n\n"
        "Traditional education systems were designed for an industrial economy. "
        "Today's knowledge economy demands critical thinking, creativity, and "
        "lifelong learning skills that many curricula still fail to cultivate.\n\n"
        "Project-based learning, personalised instruction, and competency-based "
        "progression are gaining traction in forward-thinking school districts. "
        "Technology can support — but not replace — skilled educators.\n",
        encoding="utf-8",
    )

    (d / "climate_summary.txt").write_text(
        "Global average temperatures have risen approximately 1.2 degrees Celsius "
        "above pre-industrial levels. Carbon dioxide concentrations in the atmosphere "
        "reached 420 parts per million in 2023. Renewable energy deployment is "
        "accelerating but must increase substantially to meet net-zero targets.\n",
        encoding="utf-8",
    )

    return d


@pytest.fixture
def council_dir(tmp_path: Path) -> Path:
    """Write 3 council member markdown files to tmp_path/council."""
    d = tmp_path / "council"
    d.mkdir(parents=True, exist_ok=True)

    (d / "synthesizer.md").write_text(
        "---\n"
        "name: Final Synthesizer\n"
        "persona: A thoughtful integrator who weaves perspectives into conclusions\n"
        "primary_lens: holistic synthesis\n"
        "position: 1\n"
        "role_type: synthesizer\n"
        "escalation_rule: Halt if response is incomplete\n"
        "---\n"
        "I bring together all viewpoints to produce a unified response.\n",
        encoding="utf-8",
    )

    (d / "analyst.md").write_text(
        "---\n"
        "name: Domain Analyst\n"
        "persona: A precise specialist who evaluates claims against domain knowledge\n"
        "primary_lens: domain accuracy\n"
        "position: 2\n"
        "role_type: domain_specialist\n"
        "escalation_rule: Halt if response is out of scope\n"
        "---\n"
        "I assess whether responses are grounded in relevant domain expertise.\n",
        encoding="utf-8",
    )

    (d / "critic.md").write_text(
        "---\n"
        "name: Adversarial Critic\n"
        "persona: A sharp, skeptical critic who challenges every claim with scrutiny\n"
        "primary_lens: factual accuracy\n"
        "position: 3\n"
        "role_type: critic\n"
        "escalation_rule: Halt if response contains factually false claims\n"
        "---\n"
        "I challenge every assertion with evidence-based scrutiny.\n",
        encoding="utf-8",
    )

    return d


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Return tmp_path as the data directory root."""
    return tmp_path


@pytest.fixture
def goals_dir(tmp_path: Path, council_dir: Path) -> Path:
    """Write a test-goal.md to tmp_path/goals/ and generate the manifest."""
    d = tmp_path / "goals"
    d.mkdir(parents=True, exist_ok=True)

    (d / "test-goal.md").write_text(
        "---\n"
        "desired_outcome: Provide a well-reasoned answer to the user's question\n"
        "corpus_path: corpus\n"
        "council:\n"
        "  - persona_file: synthesizer.md\n"
        "    authority_tier: 1\n"
        "  - persona_file: analyst.md\n"
        "    authority_tier: 2\n"
        "---\n"
        "Answer the user's question using the available corpus context.\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "goals_manifest.json"
    process_goals(d, council_dir, manifest_path)

    return d


@pytest.fixture
def test_config(
    tmp_path: Path,
    corpus_dir: Path,
    council_dir: Path,
    goals_dir: Path,
) -> AppConfig:
    """Return an AppConfig with all paths pointing at tmp_path-based directories.

    data_dir is set to tmp_path so that derived properties align with the
    corpus_dir (tmp_path/corpus), council_dir (tmp_path/council), and
    goals_dir (tmp_path/goals) fixtures.
    """
    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=tmp_path,
        chunk_max_size=512,
        retrieval_top_k=3,
        chroma_collection="test_corpus",
    )


@pytest.fixture
def file_store(test_config: AppConfig) -> FileStore:
    """Return a FileStore backed by the test data directory."""
    return FileStore(test_config.users_dir)


def test_conftest_imports() -> None:
    """Smoke test: verify that all fixture imports resolve correctly."""
    assert AppConfig is not None
    assert FileStore is not None
