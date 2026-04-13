from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

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


def _format_member_responses(log: list[MemberLog]) -> str:
    if not log:
        return "No member responses."
    return "\n\n".join(
        f"**Perspective {i}:**\n{entry.response}"
        for i, entry in enumerate(log, start=1)
    )


def _format_escalation_flags(log: list[MemberLog]) -> str:
    flagged = [e for e in log if e.escalation_triggered]
    if not flagged:
        return "No escalations flagged."
    return "\n".join("- escalation triggered" for _ in flagged)


def _call_member(
    member: CouncilMember,
    conversation_history: str,
    corpus_text: str,
    user_message: str,
    goal_name: str,
    goal_description: str,
    llm: LLMClient,
) -> MemberLog:
    system_prompt = llm.render_template(
        "member_system",
        {
            "member_name": member.name,
            "persona": member.persona,
            "primary_lens": member.primary_lens,
            "role_type": member.role_type,
            "goal_name": goal_name,
            "goal_description": goal_description,
        },
    )
    response = llm.call(
        "member_deliberation",
        {
            "conversation_history": conversation_history,
            "corpus_chunks": corpus_text,
            "user_message": user_message,
        },
        system_prompt=system_prompt,
    )
    escalation_response = llm.call(
        "escalation_check",
        {
            "escalation_rule": member.escalation_rule,
            "member_response": response,
        },
    )
    return MemberLog(
        member_name=member.name,
        position=member.position,
        response=response,
        escalation_triggered=escalation_response.strip().startswith("TRIGGERED"),
    )


def run_deliberation(
    user_message: str,
    corpus_chunks: list[ChunkResult],
    members: list[CouncilMember],
    llm: LLMClient,
    conversation_history: str = "",
    goal_name: str = "",
    goal_description: str = "",
) -> DeliberationResult:
    """Run the full council deliberation pipeline.

    Non-position-1 members are called concurrently via ThreadPoolExecutor.
    Position-1 synthesizes all responses after all members complete.
    If any member triggers escalation, position-1 resolves via the
    escalation_resolution template; otherwise final_synthesis is used.
    """
    sorted_members = sorted(members, key=lambda m: m.position, reverse=True)
    position_one = next(m for m in sorted_members if m.position == 1)
    others = [m for m in sorted_members if m.position != 1]

    corpus_text = _format_chunks(corpus_chunks)

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

    deliberation_log: list[MemberLog] = []

    with ThreadPoolExecutor(max_workers=len(others) if others else 1) as executor:
        futures: list[Future[MemberLog]] = [
            executor.submit(
                _call_member,
                member,
                conversation_history,
                corpus_text,
                user_message,
                goal_name,
                goal_description,
                llm,
            )
            for member in others
        ]

        for future in futures:
            try:
                log_entry = future.result()
            except Exception:
                raise
            deliberation_log.append(log_entry)

    any_escalation = any(entry.escalation_triggered for entry in deliberation_log)
    escalating_member: str | None = None
    if any_escalation:
        escalating_member = next(
            entry.member_name
            for entry in deliberation_log
            if entry.escalation_triggered
        )

    if any_escalation:
        final_response = llm.call(
            "escalation_resolution",
            {
                "conversation_history": conversation_history,
                "user_message": user_message,
                "corpus_chunks": corpus_text,
                "escalation_flags": _format_escalation_flags(deliberation_log),
                "member_responses": _format_member_responses(deliberation_log),
            },
            system_prompt=position_one_system_prompt,
        )
    else:
        final_response = llm.call(
            "final_synthesis",
            {
                "conversation_history": conversation_history,
                "user_message": user_message,
                "corpus_chunks": corpus_text,
                "member_responses": _format_member_responses(deliberation_log),
            },
            system_prompt=position_one_system_prompt,
        )

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
        escalation_triggered=any_escalation,
        escalating_member=escalating_member,
    )


__all__ = ["MemberLog", "DeliberationResult", "run_deliberation"]
