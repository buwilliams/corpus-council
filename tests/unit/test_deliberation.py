from __future__ import annotations

import shutil
from pathlib import Path

from corpus_council.core.config import AppConfig
from corpus_council.core.council import CouncilMember
from corpus_council.core.deliberation import (
    DeliberationResult,
    MemberLog,
    run_deliberation,
)
from corpus_council.core.llm import LLMClient

_TEMPLATES_SRC = Path(__file__).parent.parent.parent / "templates"


class TestLLMClient(LLMClient):
    __test__ = False  # prevent pytest from collecting this as a test suite

    def __init__(
        self,
        config: AppConfig,
        *,
        trigger_escalation_for: str | None = None,
    ) -> None:
        super().__init__(config)
        self.trigger_escalation_for = trigger_escalation_for
        self.calls: list[tuple[str, dict]] = []  # type: ignore[type-arg]
        self._last_deliberating_member: str = ""

    def call(self, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
        self.render_template(template_name, context)  # REAL rendering
        self.calls.append((template_name, context))
        if template_name == "member_deliberation":
            self._last_deliberating_member = context.get("member_name", "")
        if template_name == "escalation_check":
            member = self._last_deliberating_member
            if self.trigger_escalation_for and member == self.trigger_escalation_for:
                return "TRIGGERED: factual error detected"
            return "NOT_TRIGGERED"
        return f"Response from {context.get('member_name', template_name)}"


def _make_config(templates_dir: Path) -> AppConfig:
    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-20241022",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=templates_dir.parent / "data",
        corpus_dir=templates_dir.parent / "corpus",
        council_dir=templates_dir.parent / "council",
        templates_dir=templates_dir,
        plans_dir=templates_dir.parent / "plans",
        chunk_max_size=512,
        retrieval_top_k=3,
        chroma_collection="test_corpus",
    )


def _copy_templates(tmp_path: Path) -> Path:
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    for f in _TEMPLATES_SRC.glob("*.md"):
        shutil.copy2(f, tpl_dir / f.name)
    return tpl_dir


def _make_members() -> list[CouncilMember]:
    return [
        CouncilMember(
            name="Final Synthesizer",
            persona="A thoughtful integrator",
            primary_lens="holistic synthesis",
            position=1,
            role_type="synthesizer",
            escalation_rule="Halt if response is incomplete",
            body="I bring together all viewpoints.",
            source_file="synthesizer.md",
        ),
        CouncilMember(
            name="Domain Analyst",
            persona="A precise specialist",
            primary_lens="domain accuracy",
            position=2,
            role_type="domain_specialist",
            escalation_rule="Halt if response is out of scope",
            body="I assess domain expertise.",
            source_file="analyst.md",
        ),
        CouncilMember(
            name="Adversarial Critic",
            persona="A sharp skeptical critic",
            primary_lens="factual accuracy",
            position=3,
            role_type="critic",
            escalation_rule="Halt if response contains factually false claims",
            body="I challenge every assertion.",
            source_file="critic.md",
        ),
    ]


def test_deliberation_normal_path_iterates_members_descending(tmp_path: Path) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert isinstance(result, DeliberationResult)
    assert not result.escalation_triggered
    # log has entries for all 3 members
    assert len(result.deliberation_log) == 3
    # first in log is highest position (3), last is position 1
    assert result.deliberation_log[0].position == 3
    assert result.deliberation_log[-1].position == 1


def test_deliberation_position_1_always_runs_last(tmp_path: Path) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="Test",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    final_entry = result.deliberation_log[-1]
    assert final_entry.position == 1
    assert final_entry.member_name == "Final Synthesizer"


def test_deliberation_escalation_triggered_skips_remaining_members(
    tmp_path: Path,
) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    # Trigger escalation for position-3 (Adversarial Critic)
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    result = run_deliberation(
        user_message="What is nutrition?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert result.escalation_triggered is True
    # position-1 must still appear in the log
    position_1_entries = [e for e in result.deliberation_log if e.position == 1]
    assert len(position_1_entries) == 1
    # position-2 should NOT appear (skipped after escalation at position-3)
    position_2_entries = [e for e in result.deliberation_log if e.position == 2]
    assert len(position_2_entries) == 0


def test_deliberation_escalation_path_uses_resolution_template(
    tmp_path: Path,
) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    run_deliberation(
        user_message="What is climate?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    template_names = [name for name, _ in llm.calls]
    assert "escalation_resolution" in template_names


def test_deliberation_final_response_not_empty(tmp_path: Path) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="Tell me about education.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert result.final_response != ""


def test_deliberation_deliberation_log_has_member_name_and_position(
    tmp_path: Path,
) -> None:
    tpl_dir = _copy_templates(tmp_path)
    config = _make_config(tpl_dir)
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="Tell me about nutrition.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    for entry in result.deliberation_log:
        assert isinstance(entry, MemberLog)
        assert entry.member_name
        assert entry.position > 0
        assert isinstance(entry.response, str)
        assert isinstance(entry.escalation_triggered, bool)
