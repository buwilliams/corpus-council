from __future__ import annotations

from corpus_council.core.config import AppConfig
from corpus_council.core.conversation import run_conversation
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore


class ConvTestLLM(LLMClient):
    __test__ = False

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config)
        self.calls: list[tuple[str, dict]] = []  # type: ignore[type-arg]

    def call(self, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
        self.render_template(template_name, context)  # REAL
        self.calls.append((template_name, dict(context)))
        if template_name == "escalation_check":
            return "NOT_TRIGGERED"
        return f"Council response to: {context.get('user_message', '')[:50]}"


def test_two_turn_conversation_persists_correctly(
    test_config: AppConfig, file_store: FileStore
) -> None:
    ingest_corpus(test_config)
    embed_corpus(test_config)

    llm = ConvTestLLM(test_config)

    result1 = run_conversation(
        "user0001", "What is Python?", test_config, file_store, llm
    )
    assert result1.turn_count == 1

    result2 = run_conversation("user0001", "Tell me more", test_config, file_store, llm)
    assert result2.turn_count == 2

    records = file_store.read_jsonl(file_store.chat_messages_path("user0001"))
    assert len(records) == 2


def test_conversation_resumes_context_from_disk(
    test_config: AppConfig, file_store: FileStore
) -> None:
    llm = ConvTestLLM(test_config)

    run_conversation("user0001", "Hello world", test_config, file_store, llm)

    new_store = FileStore(test_config.data_dir)
    result2 = run_conversation(
        "user0001", "Continue please", test_config, new_store, llm
    )
    assert result2.turn_count == 2


def test_conversation_retrieves_relevant_corpus(
    test_config: AppConfig, file_store: FileStore
) -> None:
    ingest_corpus(test_config)
    embed_corpus(test_config)

    llm = ConvTestLLM(test_config)

    run_conversation(
        "user0001",
        "What do we know about artificial intelligence progress?",
        test_config,
        file_store,
        llm,
    )

    member_deliberation_calls = [
        ctx for name, ctx in llm.calls if name == "member_deliberation"
    ]
    assert len(member_deliberation_calls) > 0

    corpus_chunks_value = member_deliberation_calls[0].get("corpus_chunks", "")
    assert corpus_chunks_value != "No relevant corpus context available."
