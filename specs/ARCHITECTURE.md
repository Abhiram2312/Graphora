# ARCHITECTURE.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. System Overview

Graphora is a monorepo containing a Python backend, a Next.js frontend, shared TypeScript types, and infrastructure configuration. All services run locally via Docker Compose. LM Studio runs as a separate native process.

```
graphora/
├── apps/
│   ├── backend/          # FastAPI application (Python 3.12)
│   └── frontend/         # Next.js 14 application (TypeScript)
├── packages/
│   └── shared-types/     # Shared TypeScript type definitions
├── specs/                # SDD specification documents
├── docker-compose.yml    # Local orchestration
├── .env.example          # Credential template (no real values)
└── README.md
```

---

## 2. Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser Client                              │
│           Next.js 14 App Router + TypeScript + Anime.js            │
│           D3.js (graph viz) + Recharts (evaluation charts)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST + WebSocket/SSE
┌────────────────────────────▼────────────────────────────────────────┐
│                         FastAPI Backend                             │
│              Python 3.12, Uvicorn, Pydantic v2                     │
│          Structured logging (structlog), OpenAPI docs              │
└──┬──────────────┬──────────────┬──────────────┬─────────────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
│ Ingest   │ │ Graph    │ │ Eval     │ │ Config /         │
│ Engine   │ │ RAG      │ │ Engine   │ │ Health           │
│          │ │ Engine   │ │          │ │                  │
└──┬───────┘ └────┬─────┘ └────┬─────┘ └──────────────────┘
   │              │              │
   │        ┌─────▼──────┐      │
   │        │ LM Studio  │      │
   │        │ Connector  │      │
   │        │            │      │
   │        │ - generate │      │
   │        │ - extract  │      │
   │        │ - embed    │      │
   │        └─────┬──────┘      │
   │              │              │
   │       LM Studio (native)   │
   │       ├── Qwen3 8B         │
   │       └── Qwen3-Embed-0.6B │
   │                            │
┌──▼────────────────────────────▼──────────────────────────────────────┐
│                          Storage Layer                               │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐  ┌─────────┐ │
│  │   Qdrant    │   │   Neo4j     │   │  PostgreSQL  │  │  Redis  │ │
│  │  (Vectors)  │   │  (Graph)    │   │  (Metadata / │  │  (Job   │ │
│  │             │   │             │   │  Eval / Jobs)│  │  Queue) │ │
│  └─────────────┘   └─────────────┘   └──────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
          ↑ All storage access via protocol abstractions
```

---

## 3. Backend Structure

```
apps/backend/
├── main.py                    # FastAPI app factory, lifespan, middleware
├── config.py                  # Pydantic Settings (reads from env)
├── api/
│   ├── routers/
│   │   ├── documents.py       # Ingest, list, delete documents
│   │   ├── graph.py           # Graph query, node/edge CRUD
│   │   ├── query.py           # RAG query, strategy selection
│   │   ├── evaluation.py      # Datasets, experiments, metrics
│   │   ├── jobs.py            # Job status polling
│   │   └── health.py          # Health check
│   └── dependencies.py        # FastAPI dependency injection
├── core/
│   ├── ingest/
│   │   ├── pipeline.py        # Orchestrates ingest steps
│   │   ├── parsers/           # PDF, TXT, MD, DOCX, URL parsers
│   │   ├── chunker.py         # Text chunking strategies
│   │   └── tasks.py           # Celery task definitions
│   ├── graph_rag/
│   │   ├── retrieval/
│   │   │   ├── vector.py      # Vector similarity retrieval
│   │   │   ├── graph.py       # Graph traversal retrieval
│   │   │   ├── hybrid.py      # Hybrid retrieval
│   │   │   └── multihop.py    # Multi-hop traversal
│   │   ├── context.py         # Context assembly + provenance
│   │   ├── generator.py       # LLM generation + streaming
│   │   └── trace.py           # Execution trace builder
│   ├── extraction/
│   │   ├── extractor.py       # Entity/relation extraction orchestrator
│   │   └── prompts.py         # System and user prompt templates
│   └── evaluation/
│       ├── metrics/
│       │   ├── tier1.py       # Deterministic metrics
│       │   ├── tier2.py       # RAGAS-based metrics
│       │   └── tier3.py       # Graph-specific metrics
│       ├── runner.py          # Evaluation run orchestrator
│       └── reporter.py        # Export (JSON, CSV)
├── storage/
│   ├── protocols.py           # VectorStore, GraphStore abstract protocols
│   ├── vector/
│   │   └── qdrant.py          # Qdrant implementation of VectorStore
│   ├── graph/
│   │   └── neo4j.py           # Neo4j implementation of GraphStore
│   └── relational/
│       ├── models.py          # SQLAlchemy ORM models
│       ├── migrations/        # Alembic migration scripts
│       └── repositories/      # Data access objects per domain
├── integrations/
│   └── lmstudio/
│       ├── client.py          # OpenAI-compatible async client
│       ├── health.py          # LM Studio connectivity check
│       └── models.py          # Request/response Pydantic models
├── workers/
│   └── celery_app.py          # Celery application configuration
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/              # Mocked LM Studio, synthetic datasets
```

---

## 4. Frontend Structure

```
apps/frontend/
├── app/                       # Next.js App Router
│   ├── layout.tsx             # Root layout, theme provider
│   ├── page.tsx               # Landing page
│   ├── dashboard/page.tsx     # Dashboard
│   ├── documents/page.tsx     # Document management
│   ├── graph/page.tsx         # Knowledge graph explorer
│   ├── chat/page.tsx          # Chat interface
│   ├── trace/[id]/page.tsx    # Trace inspector
│   ├── evaluation/page.tsx    # Evaluation dashboard
│   ├── experiments/page.tsx   # Dataset and experiment management
│   ├── settings/
│   │   ├── models/page.tsx    # LM Studio configuration
│   │   └── system/page.tsx    # System settings
│   └── docs/page.tsx          # Documentation
├── components/
│   ├── graph/                 # D3 force graph, node inspector
│   ├── chat/                  # Chat UI, streaming renderer, trace panel
│   ├── evaluation/            # Metric charts, experiment comparison
│   ├── documents/             # Upload, document list, job progress
│   └── shared/                # Layout, nav, theme toggle, empty/error states
├── lib/
│   ├── api.ts                 # Type-safe API client (fetch wrappers)
│   ├── animations.ts          # Anime.js presets and helpers
│   └── hooks/                 # Custom React hooks
└── public/
```

---

## 5. Data Flow: Document Ingestion

```
User uploads file/URL
        │
        ▼
POST /api/documents/ingest
        │
        ▼
FastAPI validates request, creates Job record in PostgreSQL
        │
        ▼
Returns { job_id, status: "queued" }
        │
        ▼ (async, Celery)
┌── Parse document (PDF/TXT/MD/DOCX/URL) ──────────────────────┐
│       │                                                        │
│       ▼                                                        │
│   Chunk text (configurable size/overlap)                       │
│       │                                                        │
│       ▼                                                        │
│   Generate embeddings (Qwen3-Embedding-0.6B via LM Studio)    │
│       │                                                        │
│       ▼                                                        │
│   Write chunks + vectors to Qdrant                            │
│       │                                                        │
│       ▼                                                        │
│   Extract entities + relations (Qwen3 8B, JSON-mode prompt)   │
│       │                                                        │
│       ▼                                                        │
│   Deduplicate and merge entities with existing graph          │
│       │                                                        │
│       ▼                                                        │
│   Write nodes + edges to Neo4j                                │
│       │                                                        │
│       ▼                                                        │
│   Update Job status to "completed" in PostgreSQL              │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
Client polls GET /api/jobs/{job_id} until terminal state
```

---

## 6. Data Flow: Graph RAG Query

```
User submits query (strategy: hybrid)
        │
        ▼
POST /api/query
        │
        ▼
Build execution trace object
        │
        ├─── [Vector path] Embed query → Qdrant similarity search → top-K chunks
        │
        ├─── [Graph path] Extract entities from query → Neo4j traversal → related nodes/edges
        │
        ▼
Merge and deduplicate results → rank by combined score
        │
        ▼
Assemble context with source provenance
        │
        ▼
Build generation prompt (system + context + query)
        │
        ▼
Stream generation from LM Studio (Qwen3 8B)
        │
        ▼
Validate citations against retrieved sources
        │
        ▼
Store completed trace in PostgreSQL
        │
        ▼
Return streamed answer + trace ID to client
```

---

## 7. Storage Responsibilities

| Store | Owns | Does NOT own |
|-------|------|-------------|
| Qdrant | Chunk vectors, entity vectors, similarity search | Graph structure, document metadata |
| Neo4j | Entity nodes, relationship edges, graph traversal | Vectors, document binary content |
| PostgreSQL | Documents, chunks (text only), jobs, evaluation datasets, experiment records, traces | Vectors, graph structure |
| Redis | Celery task queue and results | Persistent application data |

---

## 8. Protocol Abstractions

### VectorStore Protocol (Python)

```python
class VectorStore(Protocol):
    async def upsert_chunks(self, chunks: list[ChunkVector]) -> None: ...
    async def search(self, query_vector: list[float], top_k: int, filters: dict | None) -> list[ScoredChunk]: ...
    async def delete_document(self, document_id: str) -> None: ...
    async def health(self) -> bool: ...
```

### GraphStore Protocol (Python)

```python
class GraphStore(Protocol):
    async def upsert_entities(self, entities: list[Entity]) -> None: ...
    async def upsert_relationships(self, rels: list[Relationship]) -> None: ...
    async def traverse(self, entity_ids: list[str], depth: int) -> SubGraph: ...
    async def search_entities(self, query: str, top_k: int) -> list[Entity]: ...
    async def delete_document(self, document_id: str) -> None: ...
    async def health(self) -> bool: ...
```

---

## 9. Infrastructure: Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `qdrant` | `qdrant/qdrant:latest` | 6333, 6334 | Vector database |
| `neo4j` | `neo4j:5-community` | 7474, 7687 | Graph database |
| `postgres` | `postgres:16-alpine` | 5432 | Relational database |
| `redis` | `redis:7-alpine` | 6379 | Celery broker |
| `api` | Built from `apps/backend/Dockerfile` | 8000 | FastAPI backend |

LM Studio and the Next.js frontend (`npm run dev`, port 3000) run natively on the host.

---

## 10. Configuration

All configuration is read from environment variables via `pydantic-settings`. No defaults for secrets.

```
# LM Studio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_GENERATION_MODEL=qwen3-8b
LMSTUDIO_EMBEDDING_MODEL=qwen3-embedding-0.6b
LMSTUDIO_EMBEDDING_DIMENSIONS=1024

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=graphora_chunks

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<required>

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://graphora:password@localhost:5432/graphora

# Redis
REDIS_URL=redis://localhost:6379/0

# App
APP_ENV=development   # development | production
LOG_LEVEL=INFO
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50
```
