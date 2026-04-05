# Product: Corpus Council

## What

Corpus Council is a general-purpose Python API that enables LLM-based conversations grounded in a curated knowledge corpus. It stores knowledge as flat files, builds vector embeddings for fast retrieval, and routes every interaction through a **hierarchical council** — a set of markdown-defined AI personas with assigned authority levels that debate and validate responses before they are returned.

It supports two interaction modes:

1. **Conversation mode** — the user asks questions, brainstorms, or seeks advice. The council draws from the corpus to answer accurately in a consistent voice.
2. **Collection mode** — the system conducts a structured, conversational interview with the user to gather specific information, following a plan defined by the council's governing persona.

The council is the core architectural feature: each persona is defined in a markdown file describing its personality, rules, and authority tier. Higher-authority voices can override or veto lower-authority ones. The council ensures responses are not only grounded in the corpus but filtered through the principles, style, and constraints that matter for a given deployment.

Corpus Council is deployed as a standalone API, not embedded in any single application — allowing any downstream platform to integrate it as its AI interaction layer.

The first production deployment is for **Family Technology Advisors**, using the published works of Dr. Michael Rich (MD, MPH) as the corpus. The platform must respond safely and accurately in his voice, counsel parents about children's screen use, and interview parents to collect structured intake data.

## Why

LLMs are powerful but general — they lack access to private or specialized knowledge, and they have no mechanism for enforcing the principled reasoning that high-stakes domains (health, safety, child development) require. A single LLM prompt cannot reliably hold a complex persona, cite a specific corpus, and apply a hierarchy of competing values simultaneously.

Corpus Council exists to close that gap. The hierarchical council architecture mirrors how expert human institutions actually make decisions: multiple perspectives, weighted authority, deliberate debate before a response is committed. No current AI platform offers this as a general-purpose, configurable layer.

For Family Technology Advisors specifically, the stakes are high: parents are seeking guidance about their children. A response that is factually wrong, tonally off, or ethically misaligned could cause real harm. The council ensures every response is vetted against Dr. Rich's corpus, his voice, and the clinical and ethical standards his work embodies — before it reaches a parent.
