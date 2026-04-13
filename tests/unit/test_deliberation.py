from __future__ import annotations

from pathlib import Path
from typing import Any

from corpus_council.core.config import AppConfig
from corpus_council.core.council import CouncilMember
from corpus_council.core.deliberation import (
    DeliberationResult,
    MemberLog,
    _format_chunks,
    run_deliberation,
)
from corpus_council.core.llm import LLMClient
from corpus_council.core.retrieval import ChunkResult


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
        self.calls: list[dict[str, Any]] = []

    def call(  # type: ignore[override]
        self,
        template_name: str,
        context: dict,  # type: ignore[type-arg]
        system_prompt: str | None = None,
    ) -> str:
        self.render_template(template_name, context)  # REAL rendering
        self.calls.append(
            {"template": template_name, "context": context, "system_prompt": system_prompt}
        )
        if template_name == "escalation_check":
            if self.trigger_escalation_for:
                escalation_rule: str = context.get("escalation_rule", "")
                member_name = self._member_name_for_rule(escalation_rule)
                if member_name == self.trigger_escalation_for:
                    return "TRIGGERED: factual error detected"
            return "NOT_TRIGGERED"
        return f"Response from {template_name}"

    def _member_name_for_rule(self, escalation_rule: str) -> str:
        """Map escalation_rule text back to the member it belongs to."""
        rule_to_name: dict[str, str] = {
            "Halt if response contains factually false claims": "Adversarial Critic",
            "Halt if response is out of scope": "Domain Analyst",
            "Halt if response is incomplete": "Final Synthesizer",
        }
        return rule_to_name.get(escalation_rule, "")


def _make_config() -> AppConfig:
    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-20241022",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=Path("/tmp/test/data"),
        corpus_dir=Path("/tmp/test/corpus"),
        council_dir=Path("/tmp/test/council"),
        plans_dir=Path("/tmp/test/plans"),
        chunk_max_size=512,
        retrieval_top_k=3,
        chroma_collection="test_corpus",
    )


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


# ---------------------------------------------------------------------------
# Existing tests (updated)
# ---------------------------------------------------------------------------


def test_deliberation_normal_path_all_members_run() -> None:
    config = _make_config()
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
    assert len(result.deliberation_log) == 3
    non_pos1_positions = {e.position for e in result.deliberation_log if e.position != 1}
    assert 2 in non_pos1_positions
    assert 3 in non_pos1_positions
    pos1_entries = [e for e in result.deliberation_log if e.position == 1]
    assert len(pos1_entries) == 1


def test_deliberation_position_1_always_runs_last() -> None:
    config = _make_config()
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


def test_deliberation_escalation_triggered_all_members_run() -> None:
    config = _make_config()
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    result = run_deliberation(
        user_message="What is nutrition?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert result.escalation_triggered is True
    position_1_entries = [e for e in result.deliberation_log if e.position == 1]
    assert len(position_1_entries) == 1
    position_2_entries = [e for e in result.deliberation_log if e.position == 2]
    assert len(position_2_entries) == 1


def test_deliberation_escalation_path_uses_resolution_template() -> None:
    config = _make_config()
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    run_deliberation(
        user_message="What is climate?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    template_names = [c["template"] for c in llm.calls]
    assert "escalation_resolution" in template_names


def test_deliberation_final_response_not_empty() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="Tell me about education.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert result.final_response != ""


def test_deliberation_deliberation_log_has_member_name_and_position() -> None:
    config = _make_config()
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


# ---------------------------------------------------------------------------
# _format_chunks
# ---------------------------------------------------------------------------


def test_format_chunks_empty_list() -> None:
    assert _format_chunks([]) == "No relevant corpus context available."


def test_format_chunks_single_chunk() -> None:
    chunk = ChunkResult(
        chunk_id="c1",
        text="This is the chunk text.",
        source_file="doc.md",
        chunk_index=0,
        distance=0.1,
    )
    result = _format_chunks([chunk])
    assert "doc.md" in result
    assert "This is the chunk text." in result


def test_format_chunks_multiple_chunks() -> None:
    c1 = ChunkResult(
        chunk_id="c1",
        text="First chunk.",
        source_file="a.md",
        chunk_index=0,
        distance=0.1,
    )
    c2 = ChunkResult(
        chunk_id="c2",
        text="Second chunk.",
        source_file="b.md",
        chunk_index=1,
        distance=0.2,
    )
    result = _format_chunks([c1, c2])
    assert "---" in result
    assert "First chunk." in result
    assert "Second chunk." in result


# ---------------------------------------------------------------------------
# Parallel execution correctness
# ---------------------------------------------------------------------------


def test_parallel_all_non_position1_members_called() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    result = run_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    positions_in_log = {e.position for e in result.deliberation_log}
    assert 2 in positions_in_log
    assert 3 in positions_in_log


def test_parallel_position1_never_in_executor_phase() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    run_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    member_deliberation_calls = [c for c in llm.calls if c["template"] == "member_deliberation"]
    assert len(member_deliberation_calls) == 2

    final_synthesis_calls = [c for c in llm.calls if c["template"] == "final_synthesis"]
    assert len(final_synthesis_calls) == 1


def test_escalation_all_members_complete_when_one_escalates() -> None:
    config = _make_config()
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    result = run_deliberation(
        user_message="What is nutrition?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    non_pos1_entries = [e for e in result.deliberation_log if e.position != 1]
    non_pos1_positions = {e.position for e in non_pos1_entries}
    assert 2 in non_pos1_positions
    assert 3 in non_pos1_positions


def test_escalation_uses_escalation_resolution_template() -> None:
    config = _make_config()
    llm = TestLLMClient(config, trigger_escalation_for="Adversarial Critic")
    members = _make_members()

    run_deliberation(
        user_message="What is climate?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    template_names = [c["template"] for c in llm.calls]
    assert "escalation_resolution" in template_names
    assert "final_synthesis" not in template_names


def test_member_responses_in_synthesis_context() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    run_deliberation(
        user_message="Tell me about education.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    synthesis_calls = [c for c in llm.calls if c["template"] == "final_synthesis"]
    assert len(synthesis_calls) == 1
    assert "member_responses" in synthesis_calls[0]["context"]


def test_system_prompt_set_on_member_deliberation_calls() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    run_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    member_deliberation_calls = [c for c in llm.calls if c["template"] == "member_deliberation"]
    assert len(member_deliberation_calls) == 2

    persona_map = {m.persona: m.name for m in members if m.position != 1}

    for call in member_deliberation_calls:
        sp = call["system_prompt"]
        assert sp is not None and sp != "", "system_prompt must be non-empty for member_deliberation"
        assert any(persona in sp for persona in persona_map), (
            f"system_prompt did not contain any member persona. Got: {sp!r}"
        )


def test_conversation_history_in_member_deliberation_context() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    history = "User: What is AI?\nAssistant: It is a broad field."

    run_deliberation(
        user_message="Tell me more.",
        corpus_chunks=[],
        members=members,
        llm=llm,
        conversation_history=history,
    )

    member_deliberation_calls = [c for c in llm.calls if c["template"] == "member_deliberation"]
    assert len(member_deliberation_calls) == 2

    for call in member_deliberation_calls:
        assert call["context"]["conversation_history"] == history


def test_goal_description_in_system_prompt() -> None:
    config = _make_config()
    llm = TestLLMClient(config)
    members = _make_members()

    run_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
        goal_description="test goal description",
    )

    member_deliberation_calls = [c for c in llm.calls if c["template"] == "member_deliberation"]
    assert len(member_deliberation_calls) == 2

    for call in member_deliberation_calls:
        sp = call["system_prompt"]
        assert sp is not None
        assert "test goal description" in sp
