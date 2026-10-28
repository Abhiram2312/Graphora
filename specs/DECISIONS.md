# DECISIONS.md — Architecture Decision Records (ADRs)

**Status:** Active
**Version:** 1.0
**Last updated:** 2026-10-28

---

## ADR-001: Use LM Studio as the Exclusive Local Model-Serving Layer

**Date:** 2026-10-28
**Status:** Approved

**Context:** The project requires local LLM inference with no dependency on external paid APIs. Multiple local serving options exist (Ollama, llama.cpp directly, vLLM, LM Studio).

**Decision:** LM Studio is the designated model-serving layer. The application connects to it via its OpenAI-compatible HTTP API.

**Consequences:**
- The application uses the `openai` Python SDK pointed at the LM Studio base URL.
- Model identifiers and the base URL are environment variables.
- The same `openai` SDK client can be pointed at OpenAI or another provider by changing env vars; no application code changes.
- LM Studio must be running separately; the application provides a clear error when it is unavailable.

---

## ADR-002: Qwen3 8B as Generation and Entity Extraction Model

**Date:** 2026-10-28
**Status:** Approved

**Context:** The developer's hardware is RTX 4070 Ti (12GB VRAM), Ryzen 7 7700X, 64GB RAM. A generation model and a separate entity extraction model were requested. Running two large models simultaneously on 12GB VRAM is impractical.

**Decision:** Qwen3 8B serves both generation and entity extraction from a single LM Studio endpoint. The distinction is made via system prompt. No second model is loaded for extraction.

**Consequences:**
- Entity extraction and generation share the same LM Studio endpoint.
- The `LMStudioConnector` accepts a `task` parameter (`generation`, `extraction`) which selects the appropriate system prompt template.
- If the developer later wants a separate extraction model, an additional endpoint config can be added without changing the connector interface.
- Qwen3 8B's instruction-following quality is sufficient for structured entity/relation extraction via JSON-mode prompts.

---

## ADR-003: Qwen3-Embedding-0.6B for Vector Embeddings

**Date:** 2026-10-28
**Status:** Approved

**Context:** A dedicated embedding model is required for semantic vector representations.

**Decision:** Qwen3-Embedding-0.6B is the designated embedding model, served via LM Studio.

**Rationale:** Compact size (0.6B parameters) means it loads alongside Qwen3 8B within the VRAM budget. Designed specifically for embedding tasks. Embedding dimension: 1024 (verify against LM Studio model card at load time).

**Consequences:**
- Qdrant collections are created with vector size 1024.
- If the embedding model is changed, the Qdrant collection must be recreated (embeddings are not cross-model compatible). A migration script will be provided.
- The embedding model identifier and base URL are environment variables.

---

## ADR-004: Qdrant as the Vector Database

**Date:** 2026-10-28
**Status:** Approved

**Context:** The system requires a vector database with hybrid retrieval (dense + sparse), metadata filtering, persistence, and simple local operation.

**Decision:** Qdrant is the vector database.

**Rationale:** Native hybrid retrieval (BM42 sparse + dense), single Docker container, Apache 2.0 license, async Python SDK, named vector support for storing chunk and entity embeddings separately.

**Abstraction:** All vector operations route through a `VectorStore` protocol. Alternative backends (Weaviate, pgvector) can be supported by implementing the protocol.

---

## ADR-005: Neo4j Community Edition as the Graph Database

**Date:** 2026-10-28
**Status:** Approved

**Context:** The system requires a persistent graph database with multi-hop traversal, Cypher query support, and simple local operation.

**Decision:** Neo4j Community Edition is the graph database.

**License handling:** Neo4j Community is GPL-3.0. The application code is Apache 2.0. The application communicates with Neo4j exclusively over the network Bolt protocol. This is a standard client-server relationship; application code does not incorporate Neo4j source. Third-party license obligations are documented in `NOTICE` and `THIRD_PARTY_LICENSES.md`.

**Abstraction:** All graph operations route through a `GraphStore` protocol. Kuzu (MIT) or FalkorDB (MIT) can replace Neo4j by implementing the protocol.

---

## ADR-006: FastAPI as the Backend Framework

**Date:** 2026-10-28
**Status:** Approved

**Context:** The backend must integrate Python AI/ML libraries (RAGAS, sentence transformers, document parsers), provide async REST and WebSocket APIs, and support structured configuration.

**Decision:** FastAPI with Python 3.12 and Uvicorn.

**Rationale:** Python-first AI/ML ecosystem, native async, Pydantic v2 validation, automatic OpenAPI generation, WebSocket support, wide community adoption.

---

## ADR-007: Next.js 14 (App Router) as the Frontend Framework

**Date:** 2026-10-28
**Status:** Approved

**Context:** The frontend requires 11 pages, server-side data fetching for dashboards, TypeScript, and integration with Anime.js and D3.js for animations and graph visualization.

**Decision:** Next.js 14 with App Router and TypeScript.

**Rationale:** App Router server components reduce client-side waterfall for dashboard pages. File-system routing covers all 11 pages cleanly. Strong ecosystem for graph visualization (D3, react-force-graph) that Anime.js can orchestrate.

---

## ADR-008: Asynchronous Ingestion with Celery and Redis

**Date:** 2026-10-28
**Status:** Approved

**Context:** The developer requested asynchronous ingestion (background job queue) since large documents and web scraping can take significant time.

**Decision:** Celery with Redis as the broker and result backend handles background ingestion jobs.

**Consequences:**
- Redis added to Docker Compose.
- Ingestion API returns a job ID immediately; the client polls `/jobs/{id}` for status.
- All ingestion steps (parse, chunk, embed, extract, graph-write) run as Celery tasks with individual status tracking.
- In testing, Celery is replaced by a synchronous test worker.

---

## ADR-009: PostgreSQL as the Relational Store

**Date:** 2026-10-28
**Status:** Approved

**Context:** Document metadata, job status, evaluation datasets, experiment records, and evaluation results require a relational store with transactions, migrations, and complex queries.

**Decision:** PostgreSQL 16 with SQLAlchemy 2 (async) and Alembic migrations.

---

## ADR-010: Apache 2.0 License for Application Code

**Date:** 2026-10-28
**Status:** Approved

**Context:** Developer selected Apache 2.0 after reviewing options.

**Decision:** The Graphora application code is licensed under Apache License 2.0. All third-party dependencies retain their own licenses. A `NOTICE` file and `THIRD_PARTY_LICENSES.md` document all runtime dependencies and their licenses.

---

## ADR-011: No Notification System in v1.0

**Date:** 2026-10-28
**Status:** Approved

**Context:** WhatsApp and email notifications were originally in scope. Developer chose to focus on core Graph RAG and evaluation functionality first.

**Decision:** No notification system in v1.0. The adapter interface (`NotificationAdapter` protocol) is defined in the codebase but no concrete adapter is implemented. This allows a future PR to add email or WhatsApp without architectural changes.

---

## ADR-012: Docker Compose for Local Development Orchestration

**Date:** 2026-10-28
**Status:** Approved

**Context:** The system has five infrastructure components (Qdrant, Neo4j, PostgreSQL, Redis, FastAPI) plus a Next.js frontend. They must start reliably on a developer's machine with one command.

**Decision:** Docker Compose orchestrates all backend services. The Next.js frontend runs natively with `npm run dev`. LM Studio runs natively as a separate process.

**Services in docker-compose.yml:** qdrant, neo4j, postgres, redis, api (FastAPI).
