# Constitution: Corpus Council

## Core Principles

1. **The council governs, not the code.** No domain rules, ethical constraints, or behavioral guardrails are hardcoded. All such decisions belong to council personas defined in markdown. The code enforces the council's architecture; the council enforces everything else.
2. **Flat files first.** If a flat file can do the job, use it. Do not introduce databases, queues, caches, or other infrastructure unless a flat file genuinely cannot meet the requirement. Embeddings are the explicit exception.
3. **General-purpose by design.** No feature, data structure, or assumption should be specific to any one deployment (including FTA). Everything deployment-specific lives in configuration and corpus files, not in code.
4. **Voice and accuracy are non-negotiable.** In conversation mode, responses must be grounded in the corpus. Fabricated or unsupported claims are a failure. In collection mode, the interview must follow the governing persona's plan faithfully.
5. **Two interfaces, one core.** The API and CLI are both first-class interfaces. All capabilities available via the API must be accessible via the CLI. Neither is a second-class citizen.

## Quality Bar

- **Minimum acceptable quality:** Every response can be traced to a corpus source or a council persona decision. Council deliberation must be auditable (loggable).
- **Definition of done:** A feature works correctly against a real corpus with a real council configuration, not just a mock. Both interaction modes (conversation and collection) are exercised. Both the API and CLI expose the feature.
- **What we never ship:** Hard-coded personas, rules, or domain logic in Python source. Infrastructure dependencies that could be replaced by a file.

## Hard Constraints

- No hardcoded behavioral rules in source code — all rules live in council persona markdown files.
- No relational database, message queue, or external service dependency unless a flat file is technically insufficient.
- Knowledge corpus, council personas, and collection plans are all defined as files — never as code or database records.
- The platform must be deployable with no external services beyond an LLM provider and a vector embedding store.
- All LLM calls must use markdown prompt templates — no inline prompt strings in Python source.
- Python throughout. No polyglot backend.

## Out of Scope — Forever

- Bundling or hard-wiring any single deployment's corpus or council (FTA or otherwise) into the core platform.
- User authentication, authorization, or session management — the calling platform owns this.
- Training or fine-tuning models — Corpus Council works with pre-trained LLMs via API only.

## Review Standards

- A spec is not complete unless it identifies which council tier(s) are involved and how the corpus is retrieved.
- Code changes touching council orchestration or embedding retrieval require explicit reasoning about performance impact.
- Any new dependency (Python package or otherwise) must be justified against the flat-file-first principle before it is added.
- All LLM prompt templates must be reviewed as markdown files — prompt logic is not buried in code.
