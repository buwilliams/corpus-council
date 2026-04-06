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


def _format_members(members: list[CouncilMember]) -> str:
    return "\n\n".join(
        f"**{m.name} (position {m.position}, {m.role_type}):**\n"
        f"Persona: {m.persona}\n"
        f"Primary lens: {m.primary_lens}\n"
        f"Escalation rule: {m.escalation_rule}"
        for m in sorted(members, key=lambda m: m.position, reverse=True)
    )


def run_consolidated_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
) -> DeliberationResult:
    """Run consolidated deliberation with exactly 2 LLM invocations.

    First: council_consolidated — all members respond in a single prompt.
    Second: evaluator_consolidated — evaluates and synthesizes the council output.
    """
    corpus_text = _format_chunks(corpus_chunks)
    members_text = _format_members(members)

    council_context: dict[str, Any] = {
        "user_message": user_message,
        "corpus_chunks": corpus_text,
        "members": members_text,
    }
    council_output = llm.call("council_consolidated", council_context)

    evaluator_context: dict[str, Any] = {
        "user_message": user_message,
        "corpus_chunks": corpus_text,
        "council_output": council_output,
    }
    final_response = llm.call("evaluator_consolidated", evaluator_context)

    # Parse member blocks from council_output.
    # Blocks are delimited by "=== MEMBER: <name> ===" and "=== END MEMBER ===".
    deliberation_log: list[MemberLog] = []
    escalation_triggered = False
    escalating_member: str | None = None
    escalation_lines: list[str] = []

    member_name_map = {m.name: m for m in members}

    raw_blocks = council_output.split("=== MEMBER:")
    # First element is preamble; elements 1+ are member blocks
    for block in raw_blocks[1:]:
        lines = block.splitlines()
        # First line: " <name> ===" -> extract name
        first_line = lines[0] if lines else ""
        name = first_line.split(" ===")[0].strip()

        # Find ESCALATION: line
        escalation_value = "NONE"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("ESCALATION:"):
                escalation_value = stripped[len("ESCALATION:") :].strip()
                break

        member_escalation = escalation_value != "NONE"

        # Find position from matching CouncilMember
        council_member = member_name_map.get(name)
        position = council_member.position if council_member is not None else 0

        # Collect response text (everything except the name line and ESCALATION line)
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
            escalation_lines.append(f"ESCALATION: {escalation_value}")
            if not escalation_triggered:
                escalation_triggered = True
                escalating_member = name

    return DeliberationResult(
        final_response=final_response,
        deliberation_log=deliberation_log,
        escalation_triggered=escalation_triggered,
        escalating_member=escalating_member,
    )


__all__ = ["run_consolidated_deliberation"]
