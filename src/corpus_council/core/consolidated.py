from __future__ import annotations

from typing import Any

from .council import CouncilMember
from .deliberation import DeliberationResult, MemberLog
from .llm import LLMClient
from .retrieval import ChunkResult


def _format_chunks(chunks: list[ChunkResult]) -> str:
    if not chunks:
        return "No relevant corpus context available."
    return "\n\n---\n\n".join(
        f"[Source: {c.source_file}, chunk {c.chunk_index}]\n{c.text}" for c in chunks
    )


def _parse_council_output(
    council_output: str,
    members: list[CouncilMember],
) -> tuple[list[MemberLog], bool, str | None, str]:
    """Parse council output blocks into MemberLog entries and escalation data.

    Returns (deliberation_log, escalation_triggered, escalating_member,
    escalation_summary).
    """
    deliberation_log: list[MemberLog] = []
    escalation_triggered = False
    escalating_member: str | None = None
    escalation_lines: list[str] = []
    member_name_map = {m.name: m for m in members}

    raw_blocks = council_output.split("=== MEMBER:")
    # First element is preamble; elements 1+ are member blocks.
    for block in raw_blocks[1:]:
        lines = block.splitlines()
        first_line = lines[0] if lines else ""
        name = first_line.split(" ===")[0].strip()

        escalation_value = "NONE"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("ESCALATION:"):
                escalation_value = stripped[len("ESCALATION:") :].strip()
                break

        member_escalation = escalation_value != "NONE"
        council_member = member_name_map.get(name)
        position = council_member.position if council_member is not None else 0

        response_lines = []
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("ESCALATION:") or stripped == "=== END MEMBER ===":
                continue
            response_lines.append(line)
        response = "\n".join(response_lines).strip()

        deliberation_log.append(
            MemberLog(
                member_name=name,
                position=position,
                response=response,
                escalation_triggered=member_escalation,
            )
        )

        if member_escalation:
            escalation_lines.append(f"{name}: {escalation_value}")
            if not escalation_triggered:
                escalation_triggered = True
                escalating_member = name

    escalation_summary = "\n".join(escalation_lines)
    return deliberation_log, escalation_triggered, escalating_member, escalation_summary


def run_consolidated_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
    goal_name: str = "",
    goal_description: str = "",
) -> DeliberationResult:
    """Run consolidated deliberation with exactly 2 LLM invocations.

    First: council_consolidated — all members respond in a single prompt.
    Second: evaluator_consolidated — synthesises the council output into a final answer.
    """
    corpus_text = _format_chunks(corpus_chunks)

    position_one = next(m for m in members if m.position == 1)
    position_one_system_prompt = llm.render_template(
        "member_system",
        {
            "member_name": position_one.name,
            "persona": position_one.persona,
            "primary_lens": position_one.primary_lens,
            "role_type": position_one.role_type,
            "goal_name": goal_name,
            "goal_description": goal_description,
        },
    )

    # Call 1: council — pass members as a list so the template can iterate attributes.
    council_context: dict[str, Any] = {
        "user_message": user_message,
        "corpus_chunks": corpus_text,
        "members": members,
    }
    council_output = llm.call("council_consolidated", council_context)

    # Parse between calls so escalation_summary is available to the evaluator.
    deliberation_log, escalation_triggered, escalating_member, escalation_summary = (
        _parse_council_output(council_output, members)
    )

    # Call 2: evaluator — use the key names the template expects.
    evaluator_context: dict[str, Any] = {
        "user_message": user_message,
        "council_responses": council_output,
        "escalation_summary": escalation_summary,
    }
    final_response = llm.call(
        "evaluator_consolidated",
        evaluator_context,
        system_prompt=position_one_system_prompt,
    )

    return DeliberationResult(
        final_response=final_response,
        deliberation_log=deliberation_log,
        escalation_triggered=escalation_triggered,
        escalating_member=escalating_member,
    )


__all__ = ["run_consolidated_deliberation"]
