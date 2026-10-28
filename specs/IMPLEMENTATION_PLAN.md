# IMPLEMENTATION_PLAN.md

**Status:** Active
**Version:** 1.0
**Last updated:** 2026-10-28

---

## Phase Status Legend

| Symbol | Meaning |
|--------|---------|
| [APPROVED] | Specifications approved, ready to implement |
| [IN PROGRESS] | Currently being implemented |
| [COMPLETE] | Implemented and verified against acceptance criteria |
| [BLOCKED] | Waiting on a dependency or decision |
| [DEFERRED] | Out of scope for current phase |

---

## Phase 1: Discovery and Specifications

**Status:** [COMPLETE]
**Goal:** Produce and approve all foundational specifications before writing code.

| Task | Status |
|------|--------|
| Discovery proposal presented | [COMPLETE] |
| Technology choices decided | [COMPLETE] |
| Model configuration locked (Qwen3 8B + Qwen3-Embedding-0.6B) | [COMPLETE] |
| License decided (Apache 2.0) | [COMPLETE] |
| PROJECT_VISION.md written | [COMPLETE] |
| REQUIREMENTS.md written | [COMPLETE] |
| ARCHITECTURE.md written | [COMPLETE] |
| DATA_MODEL.md written | [COMPLETE] |
| API_SPEC.md written | [COMPLETE] |
| GRAPH_RAG_SPEC.md written | [COMPLETE] |
| EVALUATION_SPEC.md written | [COMPLETE] |
| SECURITY_SPEC.md written | [COMPLETE] |
| DEPLOYMENT_SPEC.md written | [COMPLETE] |
| IMPLEMENTATION_PLAN.md written | [COMPLETE] |
| DECISIONS.md written | [COMPLETE] |

**Acceptance criteria:** All spec files complete, all blocking questions answered, no code written.

---

## Phase 2: Foundation

**Status:** [APPROVED]
**Goal:** Working repository skeleton with all services starting, CI passing on empty codebase, and placeholder frontend routes.

**Estimated effort:** 2-3 sessions

### 2.1 Repository Structure

| Task | Acceptance Criteria |
|------|---------------------|
| Create monorepo structure (apps/backend, apps/frontend, packages/shared-types) | `ls` shows correct directory tree |
| Initialize pyproject.toml with uv for backend | `uv sync` installs all deps without errors |
| Initialize package.json with pnpm for frontend | `pnpm install` succeeds |
| Commit .gitignore (covers .env, __pycache__, node_modules, uploads) | `git status` shows no ignored files tracked |
| Commit .env.example with all variables, no real values | File present, `grep -r "password" .env.example` returns only placeholders |
| Add LICENSE (Apache 2.0) | File present with correct SPDX identifier |
| Add NOTICE and THIRD_PARTY_LICENSES.md | Files present, Neo4j and all deps listed |

### 2.2 Infrastructure

| Task | Acceptance Criteria |
|------|---------------------|
| Write docker-compose.yml (qdrant, neo4j, postgres, redis, api) | `docker compose up -d` starts all 5 services |
| All services pass health checks | `docker compose ps` shows all services "healthy" |
| Write docker-compose.test.yml (no api service, mock data) | CI workflow uses test compose successfully |

### 2.3 Backend Foundation

| Task | Acceptance Criteria |
|------|---------------------|
| FastAPI app factory with lifespan startup/shutdown | App starts without errors |
| Pydantic Settings config reading from env | All env vars loaded; missing required vars fail fast with clear error |
| Structured logging via structlog | Every request logs request_id, method, path, status, latency |
| GET /api/v1/health endpoint | Returns 200 with all dependency statuses; returns 503 if any unhealthy |
| PostgreSQL connection (async SQLAlchemy) | Health check reports postgres status accurately |
| Neo4j connection (async driver) | Health check reports neo4j status accurately |
| Qdrant connection (async client) | Health check reports qdrant status accurately |
| Redis connection | Health check reports redis status accurately |
| LM Studio connectivity check (health only) | Health check reports lmstudio status accurately (gracefully degraded if not running) |
| Alembic migration setup (initial empty migration) | `alembic upgrade head` runs without errors |

### 2.4 Frontend Foundation

| Task | Acceptance Criteria |
|------|---------------------|
| Next.js 14 App Router initialized | `pnpm dev` starts without errors on port 3000 |
| TypeScript strict mode enabled | `pnpm typecheck` passes on empty codebase |
| All 11 routes created with placeholder content | Browser navigation hits all routes without 404 |
| Root layout with dark/light theme toggle | Toggle switches theme; both modes have correct CSS variables |
| Anime.js installed and one test animation | Single entrance animation on landing page |
| API client module (typed fetch wrappers) | Module exists with typed function signatures for all planned endpoints |
| pnpm dev runs against local backend | Frontend can reach `GET /api/v1/health` from browser |

### 2.5 CI

| Task | Acceptance Criteria |
|------|---------------------|
| GitHub Actions: lint-and-type-check workflow | Runs ruff (Python), eslint + tsc (TypeScript); passes on clean code |
| GitHub Actions: unit-tests workflow | Runs pytest with no tests yet (0 failures) |
| GitHub Actions: build-validation workflow | `pnpm build` succeeds for frontend |
| GitHub Actions: security-scan workflow (gitleaks) | No credentials detected |
| All workflows triggered on push and PR | Confirmed in Actions tab |

### Phase 2 Acceptance Criteria

- `docker compose up -d` starts all services with no errors from a clean clone + `.env`.
- `GET /localhost:8000/api/v1/health` returns 200 with all five dependency statuses.
- Frontend renders all 11 routes (placeholder content acceptable).
- All GitHub Actions workflows pass on the main branch.
- No credentials in any committed file.

---

## Phase 3: Ingestion and Storage

**Status:** [APPROVED]
**Goal:** Upload a document, chunk it, embed it, extract entities and relationships, write to all three stores, track the job.
**Prerequisite:** Qwen3 8B and Qwen3-Embedding-0.6B loaded in LM Studio.

**Estimated effort:** 3-4 sessions

| Task | Acceptance Criteria |
|------|---------------------|
| LM Studio connector: generate, embed, extract methods | Unit tests with mock HTTP pass for all three methods |
| LM Studio health check (models available) | Health endpoint accurately reflects model load status |
| Document upload API (POST /documents/ingest) | 202 returned immediately with job_id |
| Web URL ingestion API (POST /documents/ingest-url) | Public URL scraped and queued |
| Content hash deduplication | Second upload of same file returns 409 |
| PDF parser (pdfplumber) | 10-page PDF parsed to text with page numbers |
| Plain text, Markdown, DOCX parsers | Each format parsed to plain text without errors |
| Web scraper (httpx + beautifulsoup4) | HTML body text extracted, boilerplate stripped |
| Chunker (fixed-size, token-aware, overlap) | Chunks within configured size; boundaries at sentence breaks |
| Embedding generation (batched) | Chunk vectors match configured dimension (1024) |
| Qdrant upsert | Vectors queryable after ingestion |
| Entity/relation extraction (JSON-mode prompt) | Entities and relations returned as valid JSON; invalid JSON handled gracefully |
| Neo4j graph write (MERGE deduplication) | Re-ingesting same entity merges rather than duplicates |
| Job status tracking (all steps, per-step duration) | GET /jobs/{id} reflects current step and completed steps |
| Job failure handling | Failed step recorded with error; job marked failed; processing stops |
| Ingestion job Celery task | Task executes asynchronously; app remains responsive during ingestion |
| Frontend: document upload page with drag-and-drop and job progress | File uploads, progress bar polls job status, completion shown |

### Phase 3 Acceptance Criteria

- Upload a 10-page PDF: verify chunks in Qdrant, entities and relations in Neo4j, document in PostgreSQL.
- Re-upload same PDF: 409 response, no duplicate data.
- Ingest a public URL: scraped text chunked and stored.
- All job steps tracked with duration; failures surfaced in UI and API.
- Unit tests for chunker, entity JSON parsing, and graph merge logic all pass.

---

## Phase 4: Graph RAG Engine

**Status:** [APPROVED]
**Goal:** Ask a question, get a streamed answer with full provenance trace using all four retrieval strategies.

**Estimated effort:** 3-4 sessions

| Task | Acceptance Criteria |
|------|---------------------|
| Vector retrieval strategy | Top-K chunks with cosine scores returned |
| Graph traversal retrieval strategy | Entities matched, Cypher traversal executed, chunks retrieved |
| Hybrid retrieval (RRF fusion) | Combined ranked list better than either strategy alone on test query |
| Multi-hop retrieval | 2-hop traversal finds entities not directly mentioned in query |
| Metadata filtering | Document ID filter restricts retrieval to specified documents |
| Context assembly (provenance headers, window budgeting) | Context fits in 31,232 token budget; provenance headers present |
| Generation with streaming (SSE) | Answer streams progressively to frontend |
| Citation validation | Cited chunks verified against retrieved set; unverified citations flagged |
| Execution trace (all fields populated) | GET /query/{trace_id}/trace returns fully populated trace |
| Trace stored in PostgreSQL | Trace queryable after query completes |
| POST /query endpoint (non-streaming) | Returns complete answer + trace_id |
| POST /query/stream endpoint (SSE) | Streams tokens and ends with done event containing trace_id |
| GET /query/{trace_id}/trace | Returns full trace JSON |
| Frontend: chat interface with strategy selector | Strategy selectable in UI; answer renders progressively |
| Frontend: trace inspector panel | Trace panel shows chunks, entities, relationships, scores, latency |

### Phase 4 Acceptance Criteria

- Query returns answer with traceable sources for each of the four strategies.
- Execution trace is complete with all fields populated.
- Streaming renders progressively in the frontend.
- Latency is logged per component (retrieval, assembly, generation).

---

## Phase 5: Evaluation Framework

**Status:** [APPROVED]
**Goal:** Run a 20-question dataset through both pipelines, compute all three tiers of metrics, store and compare results.

**Estimated effort:** 3-4 sessions

| Task | Acceptance Criteria |
|------|---------------------|
| Evaluation dataset CRUD API | Create, read, version datasets via API |
| Evaluation question schema | All fields (question, reference, chunk_ids, entity_ids, multi_hop flag) stored |
| Tier 1 metrics implementation (Hit Rate, MRR, NDCG) | Unit tests with known inputs produce known outputs to 4 decimal places |
| Tier 1 entity extraction P/R/F1 | Unit tests pass |
| Tier 1 latency and token aggregation | Correct mean/p90/p99 computed over dataset |
| RAGAS integration (Tier 2, disabled by default) | When enabled with judge model, faithfulness score computed and stored |
| Tier 3 metrics (multi-hop success, graph evidence coverage, provenance completeness) | Each computed correctly per spec formula |
| Experiment runner (Celery task) | Runs all questions, stores results, updates experiment status |
| Experiment config snapshot | Every experiment stores complete config at time of run |
| Experiment comparison (GET /evaluation/compare) | Delta table with winner per metric |
| Export (JSON and CSV) | Both formats downloadable and complete |
| CI evaluation regression workflow | Runs in < 15 minutes with mock client, thresholds checked |
| Synthetic dataset fixture (20 questions) | Committed to repo, used by CI |
| Mock LM Studio client | Returns deterministic responses from fixture files |
| Frontend: evaluation dashboard | Charts for aggregate metrics, per-question result table |
| Frontend: experiment comparison view | Side-by-side metric table with deltas |
| Frontend: dataset management | Create dataset, add questions, view versions |

### Phase 5 Acceptance Criteria

- All Tier 1 metric unit tests pass with 100% accuracy on known-input/known-output fixtures.
- CI evaluation regression runs in under 15 minutes with mocked model.
- Comparison report shows correct deltas between two experiment runs.
- Export produces valid JSON and CSV files.

---

## Phase 6: Frontend Experience

**Status:** [APPROVED]
**Goal:** All 11 pages fully functional with real data, Anime.js animations, light/dark themes, responsive layout.

**Estimated effort:** 4-5 sessions

| Task | Acceptance Criteria |
|------|---------------------|
| Landing page | Explains project, links to relevant pages, no fake stats or testimonials |
| Dashboard | Live counts (docs, entities, relations, experiments), recent activity |
| Document management | Upload, list, delete, status tracking, per-document chunk count |
| Knowledge graph explorer (D3 force-directed) | Click node to expand neighbors, hover for detail, Cypher query input |
| Chat interface | Strategy selector, streaming answer, inline citations |
| Trace inspector | Full trace view with all fields, color-coded components |
| Evaluation dashboard | Metric charts (Recharts), per-question result table |
| Dataset and experiment management | Create/version datasets, run experiments, view status |
| LM Studio configuration page | Shows health status, model availability, update base URL |
| System settings | Chunking defaults, collection name, log level |
| Documentation page | Setup guide, API reference link, contribution guide |
| Anime.js animations (page transitions, stagger reveals, metric counters) | Animations run; `prefers-reduced-motion` disables them |
| Light/dark theme (both fully functional) | All pages correct in both themes, WCAG AA contrast verified |
| Responsive layout (375px to 1440px) | No horizontal overflow, all content accessible at 375px |
| Empty, loading, and error states on all data pages | Visually distinct states for each condition |

### Phase 6 Acceptance Criteria

- All 11 pages functional with real data from Phases 3-5.
- Graph explorer interactive with a 500-node graph.
- Animations do not block interaction; reduced-motion respected.
- Both themes pass contrast checks.
- Mobile layout correct at 375px.

---

## Phase 7: Open-Source Release Preparation

**Status:** [APPROVED]
**Goal:** Repository ready for public open-source release.

**Estimated effort:** 1-2 sessions

| Task | Acceptance Criteria |
|------|---------------------|
| README complete (setup, architecture summary, screenshots) | Developer can follow README from scratch to running system |
| CONTRIBUTING.md | PR process, code style, issue reporting documented |
| CODE_OF_CONDUCT.md | Contributor Covenant or equivalent |
| SECURITY.md | Vulnerability disclosure process documented |
| GitHub issue templates (bug report, feature request) | Templates appear in GitHub Issues UI |
| GitHub PR template | Template appears in GitHub PR UI |
| THIRD_PARTY_LICENSES.md complete | All runtime deps listed with license and version |
| NOTICE file complete | Apache 2.0 requirements met |
| gitleaks CI scan confirms no credentials in history | CI scan passes on full commit history |
| docker-compose up verified from clean clone | Step-by-step tested on clean machine/VM |
| API documentation accessible (FastAPI /docs) | OpenAPI UI reachable at /docs |
| GitHub Actions: all workflows passing on main | All CI checks green |

### Phase 7 Acceptance Criteria

- A developer with no prior knowledge of the project can clone, run, and use the system following only the README.
- All CI workflows pass.
- No credentials or sensitive data in repository history.

---

## Known Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Qwen3-Embedding-0.6B dimension not 1024 | Startup check verifies actual dimension; fails fast with clear error |
| LM Studio model identifier differs from expected | Config validation at startup; LMSTUDIO_GENERATION_MODEL is configurable |
| Neo4j Community memory limits on large graphs | Neo4j memory settings documented in docker-compose.yml; default heap 512MB |
| RAGAS version API changes | RAGAS pinned to specific version in pyproject.toml |
| Celery task failure leaves job in running state | Celery task result expiry + job timeout (30 min) marks stalled jobs as failed |

---

## Completion Tracking

| Phase | Spec approved | Implementation started | Implementation complete | Acceptance verified |
|-------|--------------|----------------------|------------------------|-------------------|
| 1 | Yes | Yes | Yes | Yes |
| 2 | Yes | No | No | No |
| 3 | Yes | No | No | No |
| 4 | Yes | No | No | No |
| 5 | Yes | No | No | No |
| 6 | Yes | No | No | No |
| 7 | Yes | No | No | No |
