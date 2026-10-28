# REQUIREMENTS.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. Functional Requirements

### 1.1 Model Integration (LM Studio)

| ID | Requirement |
|----|-------------|
| FR-M1 | The system connects to a local LM Studio server via its OpenAI-compatible HTTP API. |
| FR-M2 | The LM Studio base URL, generation model identifier, and embedding model identifier are configurable via environment variables without code changes. |
| FR-M3 | The system validates LM Studio connectivity and model availability at startup. |
| FR-M4 | The system provides a clear, structured error when LM Studio is unavailable or the requested model is not loaded. |
| FR-M5 | The system supports streaming generation responses from LM Studio. |
| FR-M6 | The system records the model identifiers and configuration snapshot used in every experiment for reproducibility. |
| FR-M7 | Qwen3 8B is used for both answer generation and entity/relationship extraction via task-specific system prompts. |
| FR-M8 | Qwen3-Embedding-0.6B is used for all vector embedding operations. |

### 1.2 Document Ingestion

| ID | Requirement |
|----|-------------|
| FR-I1 | Users can upload documents in PDF, plain text (.txt), Markdown (.md), and Word (.docx) formats. |
| FR-I2 | Users can submit a web URL for scraping and ingestion. |
| FR-I3 | The ingestion pipeline is asynchronous: the API returns a job ID immediately, and the client polls for status. |
| FR-I4 | Each ingestion job tracks: status (queued, processing, completed, failed), start time, completion time, per-step duration, and error details on failure. |
| FR-I5 | The pipeline deduplicates documents by content hash; re-ingesting an identical document is a no-op with a clear response. |
| FR-I6 | Document chunking strategy (chunk size, overlap) is configurable per ingestion request or via default configuration. |
| FR-I7 | Each chunk stores: chunk text, chunk index, source document ID, character offsets, and embedding vector. |
| FR-I8 | Entity and relationship extraction runs on each chunk using Qwen3 8B with a structured JSON-mode prompt. |
| FR-I9 | Extracted entities are deduplicated and merged across chunks within the same document. |
| FR-I10 | The knowledge graph is updated incrementally; ingesting a new document does not rebuild the full graph. |
| FR-I11 | Ingestion failures are logged with the failing step and error, surfaced in the UI and job status API. |

### 1.3 Knowledge Graph

| ID | Requirement |
|----|-------------|
| FR-G1 | The graph stores entities as nodes with type, name, description, confidence score, source document references, and timestamps. |
| FR-G2 | The graph stores relationships as edges with type, source entity, target entity, description, confidence score, and source references. |
| FR-G3 | Entity types and relationship types are configurable; the schema is not hardcoded to a domain. |
| FR-G4 | Every graph element maintains provenance: which document(s) and which chunk(s) it was extracted from. |
| FR-G5 | The graph supports multi-hop traversal queries (depth configurable, default: 2 hops). |
| FR-G6 | Users can browse the knowledge graph visually: force-directed layout, click to expand a node's relationships, hover for detail. |
| FR-G7 | Users can execute raw Cypher queries through the UI graph explorer. |

### 1.4 Retrieval

| ID | Requirement |
|----|-------------|
| FR-R1 | The system supports four retrieval strategies, selectable per query: (a) vector similarity only, (b) graph traversal only, (c) hybrid vector+graph, (d) multi-hop graph. |
| FR-R2 | Vector retrieval returns the top-K most similar chunks with similarity scores (K configurable, default: 5). |
| FR-R3 | Graph retrieval matches entities mentioned in the query and traverses their relationships to assemble relevant context. |
| FR-R4 | Hybrid retrieval combines vector and graph results; the merge strategy (score fusion, interleaving) is configurable. |
| FR-R5 | Multi-hop retrieval follows relationship chains beyond directly matched entities up to the configured depth. |
| FR-R6 | Metadata filters (document ID, entity type, date range) can be applied to any retrieval strategy. |
| FR-R7 | Retrieved context includes source provenance (document name, page, chunk index) for every item. |

### 1.5 Generation and Execution Trace

| ID | Requirement |
|----|-------------|
| FR-A1 | Every query produces a structured execution trace containing: query text, retrieval strategy used, retrieved chunks with scores, matched entities, traversed graph relationships, assembled context, generated answer, source citations, total latency, retrieval latency, generation latency, and token usage. |
| FR-A2 | Responses stream progressively to the frontend via WebSocket or SSE. |
| FR-A3 | The execution trace is stored in PostgreSQL and retrievable by query ID. |
| FR-A4 | Users can inspect the full trace in a dedicated trace inspector view. |
| FR-A5 | The system compares Graph RAG and vector RAG answers for the same query when requested. |

### 1.6 Evaluation

| ID | Requirement |
|----|-------------|
| FR-E1 | Users can create evaluation datasets containing questions, reference answers, and relevant source references. |
| FR-E2 | Datasets are versioned; a new version is created on edit rather than overwriting the existing record. |
| FR-E3 | Users can run an evaluation experiment against a named dataset, selecting the retrieval strategy and model config. |
| FR-E4 | The system computes Tier 1 (deterministic) metrics: Hit Rate@K, MRR, NDCG@K, entity extraction precision/recall, end-to-end latency, token usage. |
| FR-E5 | The system computes Tier 2 (RAGAS-based) metrics when a judge model is configured: faithfulness, answer relevance, answer correctness, context relevance. |
| FR-E6 | The system computes Tier 3 (graph-specific) metrics: multi-hop retrieval success, graph evidence coverage, provenance completeness. |
| FR-E7 | Each evaluation run stores a configuration snapshot (model IDs, retrieval strategy, chunking config, RAGAS version) for reproducibility. |
| FR-E8 | Users can compare two evaluation runs side by side with delta values and pass/fail status per metric. |
| FR-E9 | Evaluation results are exportable as JSON and CSV. |
| FR-E10 | CI-compatible evaluation fixtures exist: a 20-question synthetic dataset with deterministic expected outputs and a mocked LM Studio client. |
| FR-E11 | The GitHub Actions evaluation regression workflow uses only mocked model responses; it never calls a real LM Studio instance. |

### 1.7 Frontend

| ID | Requirement |
|----|-------------|
| FR-U1 | The frontend has 11 pages: landing, dashboard, document management, knowledge graph explorer, chat interface, trace inspector, evaluation dashboard, dataset and experiment management, LM Studio configuration, system settings, and documentation. |
| FR-U2 | Anime.js is the primary animation library for page transitions, staggered reveals, metric transitions, graph animations, loading states, and micro-interactions. |
| FR-U3 | The UI provides light and dark themes with a working toggle. Both themes meet WCAG AA contrast requirements. |
| FR-U4 | The UI is fully responsive down to 375px viewport width. |
| FR-U5 | All interactive elements are keyboard-accessible and have visible focus indicators. |
| FR-U6 | The system respects the `prefers-reduced-motion` media query: animations are disabled or reduced when set. |
| FR-U7 | Every data-displaying view has an empty state, a loading state, and an error state. |

---

## 2. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Performance | End-to-end query latency (retrieval + generation) is logged per component. No hard threshold in v1.0 given hardware variability; latency is tracked and compared across experiments. |
| NFR-2 | Reliability | The ingestion pipeline retries transient failures (LM Studio unavailable, network timeout) up to 3 times with exponential backoff before marking a job as failed. |
| NFR-3 | Observability | All backend services emit structured JSON logs with request ID, timestamp, level, service name, and relevant context. |
| NFR-4 | Security | No credentials, tokens, or API keys are logged. All secrets are read from environment variables. `.env` is gitignored. |
| NFR-5 | Reproducibility | Every experiment stores a complete configuration snapshot. Re-running the same experiment with the same config and dataset must produce the same deterministic metrics. |
| NFR-6 | Maintainability | Vector store and graph store access is mediated by protocol classes. Swapping a backend requires only a new protocol implementation, no changes to retrieval or ingestion logic. |
| NFR-7 | Testing | All Tier 1 metric calculations have unit tests with known-input/known-output test cases. All API endpoints have integration tests. |
| NFR-8 | Licensing | Application code is Apache 2.0. All runtime dependency licenses are documented. No GPL code is incorporated into the application source. |
| NFR-9 | Local-first | The complete platform runs on a developer's machine using Docker Compose and LM Studio. No external service account is required for any core feature. |

---

## 3. Constraints

- LM Studio must be running locally before any inference-dependent feature works.
- Qwen3 8B and Qwen3-Embedding-0.6B must be loaded in LM Studio before ingestion or querying.
- Docker and Docker Compose must be installed for backend services.
- Node.js 20+ required for the frontend.
- Python 3.12+ required if running the backend outside Docker.
- Neo4j Community Edition is used as a networked service; the application code does not incorporate Neo4j source.

---

## 4. Assumptions

- The developer's RTX 4070 Ti (12GB VRAM) can run Qwen3 8B + Qwen3-Embedding-0.6B concurrently within the VRAM budget using appropriate quantization in LM Studio.
- LM Studio exposes a single OpenAI-compatible endpoint; model switching for extraction vs. generation is handled by prompt, not by separate endpoints (single model loaded).
- The primary use case at launch is corpora of tens to low hundreds of documents; no distributed ingestion is needed.
- Web scraping is for public URLs that do not require authentication.

---

## 5. Acceptance Criteria (System-Level)

| ID | Criterion |
|----|-----------|
| AC-1 | `docker-compose up` starts all services with no errors from a clean clone. |
| AC-2 | A 10-page PDF can be uploaded, ingested, and queried end-to-end within 5 minutes on the target hardware (excluding LM Studio loading time). |
| AC-3 | All GitHub Actions CI checks pass on the main branch. |
| AC-4 | The CI evaluation regression completes in under 15 minutes using mocked model responses. |
| AC-5 | The knowledge graph explorer renders and is interactive for a graph with up to 500 nodes. |
| AC-6 | Every UI page has empty, loading, and error states implemented and visually distinct. |
| AC-7 | No credentials appear in any committed file (verified by gitleaks in CI). |
| AC-8 | All Tier 1 evaluation metric unit tests pass with 100% accuracy on known-input/known-output fixtures. |
