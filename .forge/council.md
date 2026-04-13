# Council

## Roles

- **programmer** — Implements Python code across all core modules, API, and CLI; also implements vanilla HTML/JS frontend
- **tester** — Writes and validates the test suite; ensures coverage and real-implementation requirements are met
- **product-manager** — Ensures deliverables align with the product spec and constitution; guards against scope creep and model drift; verifies no old query/conversation/collection concepts survive in any interface
- **api-designer** — Owns the FastAPI endpoint contracts, request/response shapes, HTTP status codes, and CLI interface design; ensures REST and CLI surfaces are coherent and consistent
- **data-engineer** — Owns the flat-file store design, sharding strategy, fcntl locking, JSONL/JSON schemas, and ChromaDB integration
- **security-engineer** — Reviews API key handling, file I/O safety, input validation, and path traversal risks at system boundaries
- **ux-engineer** — Owns the frontend 3-tab Goals/Files/Admin layout; ensures Goals chat UX is clear and wires correctly to POST /chat; removes all obsolete tab code
- **concurrency-engineer** — Owns thread-safety, ThreadPoolExecutor usage, and any concurrency-related risks in the parallel deliberation implementation
- **prompt-engineer** — Owns all LLM prompt templates; ensures single-persona framing throughout, no deliberation-structure leakage, and position-1 persona consistency across both deliberation modes
