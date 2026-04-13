from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from corpus_council.core.consolidated import run_consolidated_deliberation
from corpus_council.core.council import CouncilMember
from corpus_council.core.deliberation import DeliberationResult
from corpus_council.core.llm import LLMClient


def _make_config() -> Any:
    from corpus_council.core.config import AppConfig

    return AppConfig(
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        data_dir=Path("/tmp/test/data"),
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


def _make_normal_council_output(members: list[CouncilMember]) -> str:
    """Build a valid council output stub with no escalations."""
    blocks = []
    for m in sorted(members, key=lambda m: m.position, reverse=True):
        blocks.append(
            f"=== MEMBER: {m.name} ===\n"
            f"This is a response from {m.name}.\n"
            f"ESCALATION: NONE\n"
            f"=== END MEMBER ==="
        )
    return "\n\n".join(blocks)


def _make_escalating_council_output(
    members: list[CouncilMember],
    escalating_name: str,
    escalation_msg: str,
) -> str:
    """Build a council output stub where one member triggers an escalation."""
    blocks = []
    for m in sorted(members, key=lambda m: m.position, reverse=True):
        if m.name == escalating_name:
            escalation_line = escalation_msg
        else:
            escalation_line = "NONE"
        blocks.append(
            f"=== MEMBER: {m.name} ===\n"
            f"This is a response from {m.name}.\n"
            f"ESCALATION: {escalation_line}\n"
            f"=== END MEMBER ==="
        )
    return "\n\n".join(blocks)


def test_council_consolidated_template_renders_all_personas() -> None:
    """Real render_template() renders council_consolidated with all member personas."""
    config = _make_config()
    llm = LLMClient(config)
    members = _make_members()

    rendered = llm.render_template(
        "council_consolidated",
        {
            "user_message": "What is AI?",
            "corpus_chunks": "No relevant corpus context available.",
            "members": members,
        },
    )

    for m in members:
        assert m.name in rendered
        assert m.persona in rendered


def test_evaluator_consolidated_template_renders_inputs() -> None:
    """Real render_template() renders evaluator_consolidated with user_message."""
    config = _make_config()
    llm = LLMClient(config)

    user_message = "Explain machine learning."
    council_output = (
        "=== MEMBER: Domain Analyst ===\n"
        "Some analysis.\n"
        "ESCALATION: NONE\n"
        "=== END MEMBER ==="
    )

    rendered = llm.render_template(
        "evaluator_consolidated",
        {
            "user_message": user_message,
            "council_responses": council_output,
            "escalation_summary": "",
        },
    )

    assert user_message in rendered
    assert "Domain Analyst" in rendered


def test_run_consolidated_deliberation_makes_exactly_two_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub LLMClient.call; assert exactly 2 calls with correct template names."""
    config = _make_config()
    llm = LLMClient(config)
    members = _make_members()

    calls: list[tuple[str, dict[str, Any]]] = []
    council_output = _make_normal_council_output(members)

    def fake_call(self: LLMClient, template_name: str, context: dict[str, Any]) -> str:
        calls.append((template_name, context))
        if template_name == "council_consolidated":
            return council_output
        return "Final synthesized answer."

    monkeypatch.setattr(LLMClient, "call", fake_call)

    run_consolidated_deliberation(
        user_message="What is AI?",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert len(calls) == 2
    assert calls[0][0] == "council_consolidated"
    assert calls[1][0] == "evaluator_consolidated"


def test_run_consolidated_deliberation_returns_deliberation_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub LLMClient.call; assert result is DeliberationResult with non-empty body."""
    config = _make_config()
    llm = LLMClient(config)
    members = _make_members()

    council_output = _make_normal_council_output(members)

    def fake_call(self: LLMClient, template_name: str, context: dict[str, Any]) -> str:
        if template_name == "council_consolidated":
            return council_output
        return "Final synthesized answer from evaluator."

    monkeypatch.setattr(LLMClient, "call", fake_call)

    result = run_consolidated_deliberation(
        user_message="Tell me about nutrition.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert isinstance(result, DeliberationResult)
    assert result.final_response != ""


def test_run_consolidated_deliberation_extracts_escalation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub escalation from Domain Analyst; verify escalation fields and context."""
    config = _make_config()
    llm = LLMClient(config)
    members = _make_members()

    escalation_msg = "Response is out of scope"
    council_output = _make_escalating_council_output(
        members, "Domain Analyst", escalation_msg
    )

    evaluator_contexts: list[dict[str, Any]] = []

    def fake_call(self: LLMClient, template_name: str, context: dict[str, Any]) -> str:
        if template_name == "council_consolidated":
            return council_output
        evaluator_contexts.append(context)
        return "Escalation-aware final answer."

    monkeypatch.setattr(LLMClient, "call", fake_call)

    result = run_consolidated_deliberation(
        user_message="Tell me something off-topic.",
        corpus_chunks=[],
        members=members,
        llm=llm,
    )

    assert result.escalation_triggered is True
    assert result.escalating_member == "Domain Analyst"

    assert len(evaluator_contexts) == 1
    ctx = evaluator_contexts[0]
    assert "out of scope" in ctx.get("council_responses", "")
    assert "out of scope" in ctx.get("escalation_summary", "")
