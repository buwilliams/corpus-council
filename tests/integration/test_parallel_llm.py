"""Integration tests for parallel deliberation that call a real LLM.

These tests are marked @pytest.mark.llm and require ANTHROPIC_API_KEY to be set.
Run with: uv run pytest tests/integration/test_parallel_llm.py -m llm
"""

from __future__ import annotations

import pytest

from corpus_council.core.config import AppConfig
from corpus_council.core.council import load_council
from corpus_council.core.deliberation import run_deliberation
from corpus_council.core.llm import LLMClient


@pytest.mark.llm
def test_parallel_deliberation_end_to_end(test_config: AppConfig) -> None:
    """Real LLM: all council members run in parallel and produce a final response."""
    llm = LLMClient(test_config)
    members = load_council(test_config)

    result = run_deliberation(
        user_message="What are the key factors in good nutrition?",
        corpus_chunks=[],
        members=members,
        llm=llm,
        conversation_history="User: Hello\nAssistant: Hi",
        goal_name="test-goal",
        goal_description="Help the user",
    )

    assert result.final_response, "final_response must be a non-empty string"
    assert isinstance(result.final_response, str)
    assert len(result.final_response) > 0

    # All non-position-1 members appear in the deliberation log
    non_pos1_positions = {e.position for e in result.deliberation_log if e.position != 1}
    all_member_positions = {m.position for m in members if m.position != 1}
    assert non_pos1_positions == all_member_positions, (
        f"Expected all non-position-1 members in log. "
        f"Expected positions: {all_member_positions}, got: {non_pos1_positions}"
    )

    # Position-1 is always in the log
    pos1_entries = [e for e in result.deliberation_log if e.position == 1]
    assert len(pos1_entries) == 1, "Position-1 member must appear exactly once in the log"

    # escalation_triggered is a valid bool (either value is acceptable)
    assert isinstance(result.escalation_triggered, bool)

    # The normal (non-escalation) path should not be triggered for a benign query
    assert result.escalation_triggered is False


@pytest.mark.llm
def test_parallel_deliberation_position1_always_in_log(test_config: AppConfig) -> None:
    """Real LLM: position-1 member always produces a final response regardless of content."""
    llm = LLMClient(test_config)
    members = load_council(test_config)

    result = run_deliberation(
        user_message="Explain the basics of artificial intelligence in simple terms.",
        corpus_chunks=[],
        members=members,
        llm=llm,
        goal_name="test-goal",
        goal_description="Answer user questions clearly and accurately",
    )

    # final_response is non-empty regardless of escalation state
    assert result.final_response, "final_response must be a non-empty string"

    # Position-1 always contributes to the log
    pos1_entries = [e for e in result.deliberation_log if e.position == 1]
    assert len(pos1_entries) == 1

    # All log entries have valid structure
    for entry in result.deliberation_log:
        assert entry.member_name, "member_name must be non-empty"
        assert entry.position > 0, "position must be positive"
        assert isinstance(entry.response, str), "response must be a string"
        assert isinstance(entry.escalation_triggered, bool), "escalation_triggered must be bool"
