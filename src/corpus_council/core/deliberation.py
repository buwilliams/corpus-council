from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .council import CouncilMember
from .llm import LLMClient
from .retrieval import ChunkResult


@dataclass
class MemberLog:
    member_name: str
    position: int
    response: str
    escalation_triggered: bool


@dataclass
class DeliberationResult:
    final_response: str
    deliberation_log: list[MemberLog]
    escalation_triggered: bool
    escalating_member: str | None


def _format_chunks(chunks: list[ChunkResult]) -> str:
    if not chunks:
        return "No relevant corpus context available."
    return "\n\n---\n\n".join(
        f"[Source: {c.source_file}, chunk {c.chunk_index}]\n{c.text}" for c in chunks
    )


def _format_prior_responses(log: list[MemberLog]) -> str:
    if not log:
        return "No prior responses."
    return "\n\n".join(
        f"**{entry.member_name} (position {entry.position}):**\n{entry.response}"
        for entry in log
    )


def run_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
) -> DeliberationResult:
    """Run the full council deliberation pipeline.

    Members are iterated from highest position to lowest (position-1 is last).
    If any member triggers escalation, remaining non-position-1 members are
    skipped and position-1 resolves via the escalation template. Otherwise
    position-1 synthesizes normally.
    """
    sorted_members = sorted(members, key=lambda m: m.position, reverse=True)
    position_one = next(m for m in sorted_members if m.position == 1)
    others = [m for m in sorted_members if m.position != 1]

    deliberation_log: list[MemberLog] = []
    escalation_triggered = False
    escalating_member: str | None = None
    escalation_reason: str = ""

    corpus_text = _format_chunks(corpus_chunks)

    for member in others:
        prior_responses = _format_prior_responses(deliberation_log)

        member_context: dict[str, Any] = {
            "member_name": member.name,
            "persona": member.persona,
            "primary_lens": member.primary_lens,
            "role_type": member.role_type,
            "user_message": user_message,
            "corpus_chunks": corpus_text,
            "prior_responses": prior_responses,
        }
        response = llm.call("member_deliberation", member_context)

        escalation_context: dict[str, Any] = {
            "escalation_rule": member.escalation_rule,
            "member_response": response,
        }
        escalation_response = llm.call("escalation_check", escalation_context)

        if escalation_response.startswith("TRIGGERED"):
            deliberation_log.append(
                MemberLog(
                    member_name=member.name,
                    position=member.position,
                    response=response,
                    escalation_triggered=True,
                )
            )
            escalation_triggered = True
            escalating_member = member.name
            escalation_reason = escalation_response
            break
        else:
            deliberation_log.append(
                MemberLog(
                    member_name=member.name,
                    position=member.position,
                    response=response,
                    escalation_triggered=False,
                )
            )

    if escalation_triggered:
        escalation_log_text = (
            f"Escalation triggered by {escalating_member}. Reason: {escalation_reason}"
        )
        resolution_context: dict[str, Any] = {
            "user_message": user_message,
            "corpus_chunks": corpus_text,
            "escalation_log": escalation_log_text,
            "prior_responses": _format_prior_responses(deliberation_log),
        }
        final_response = llm.call("escalation_resolution", resolution_context)
    else:
        synthesis_context: dict[str, Any] = {
            "member_name": position_one.name,
            "persona": position_one.persona,
            "primary_lens": position_one.primary_lens,
            "role_type": position_one.role_type,
            "user_message": user_message,
            "corpus_chunks": corpus_text,
            "deliberation_log": _format_prior_responses(deliberation_log),
        }
        final_response = llm.call("final_synthesis", synthesis_context)

    deliberation_log.append(
        MemberLog(
            member_name=position_one.name,
            position=position_one.position,
            response=final_response,
            escalation_triggered=False,
        )
    )

    return DeliberationResult(
        final_response=final_response,
        deliberation_log=deliberation_log,
        escalation_triggered=escalation_triggered,
        escalating_member=escalating_member,
    )


__all__ = ["MemberLog", "DeliberationResult", "run_deliberation"]
