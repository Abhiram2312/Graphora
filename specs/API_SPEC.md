# API_SPEC.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

Base URL: `http://localhost:8000/api/v1`
Content-Type: `application/json` (unless noted)
All timestamps: ISO 8601, UTC.

---

## 1. Health

### GET /health

Returns the health status of all backend dependencies.

**Response 200**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "dependencies": {
    "qdrant": "healthy",
    "neo4j": "healthy",
    "postgres": "healthy",
    "redis": "healthy",
    "lmstudio": "healthy"
  }
}
```

If any dependency is unhealthy, `status` is `"degraded"` and the HTTP status code is `503`.

---

## 2. Documents

### POST /documents/ingest (multipart/form-data)

Upload a file for ingestion.

**Request fields:**
- `file` (required): binary file upload
- `chunk_size` (optional, int, default 512): target chunk token size
- `chunk_overlap` (optional, int, default 50): overlap between adjacent chunks

**Response 202**
```json
{
  "job_id": "uuid",
  "document_id": "uuid",
  "status": "queued",
  "message": "Ingestion job queued."
}
```

**Response 409** (duplicate document)
```json
{
  "error": "duplicate_document",
  "message": "A document with this content hash already exists.",
  "existing_document_id": "uuid"
}
```

---

### POST /documents/ingest-url

Ingest a web URL.

**Request body:**
```json
{
  "url": "https://example.com/article",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

**Response:** Same as POST /documents/ingest.

---

### GET /documents

List all documents.

**Query params:** `status` (filter by ingestion status), `page` (int, default 1), `page_size` (int, default 20)

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "report.pdf",
      "source_type": "pdf",
      "status": "completed",
      "page_count": 10,
      "chunk_count": 42,
      "created_at": "2026-10-28T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### GET /documents/{document_id}

Get a single document with its chunks.

**Response 200**
```json
{
  "id": "uuid",
  "filename": "report.pdf",
  "status": "completed",
  "metadata": {},
  "chunks": [
    {
      "id": "uuid",
      "chunk_index": 0,
      "text": "...",
      "char_start": 0,
      "char_end": 512,
      "page_number": 1
    }
  ]
}
```

---

### DELETE /documents/{document_id}

Delete a document, its chunks, vectors, and all associated graph nodes that have no other source.

**Response 200**
```json
{ "message": "Document and associated data deleted." }
```

---

## 3. Jobs

### GET /jobs/{job_id}

Poll ingestion job status.

**Response 200**
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "status": "running",
  "current_step": "embed",
  "steps_completed": {
    "parse": { "status": "completed", "duration_ms": 120 },
    "chunk": { "status": "completed", "duration_ms": 45 },
    "embed": { "status": "running", "duration_ms": null }
  },
  "error_message": null,
  "queued_at": "2026-10-28T10:00:00Z",
  "started_at": "2026-10-28T10:00:01Z",
  "completed_at": null
}
```

---

## 4. Graph

### GET /graph/entities

Search entities in the knowledge graph.

**Query params:** `q` (text search), `type` (entity type filter), `document_id` (filter by source doc), `page`, `page_size`

**Response 200**
```json
{
  "items": [
    {
      "id": "neo4j-node-id",
      "name": "Qwen3",
      "type": "Concept",
      "description": "A family of language models by Alibaba.",
      "confidence": 0.95,
      "source_document_ids": ["uuid"],
      "source_chunk_ids": ["uuid"]
    }
  ],
  "total": 1
}
```

---

### GET /graph/entities/{entity_id}/neighbors

Get the entity and its neighborhood (for graph visualization).

**Query params:** `depth` (int, default 1, max 3)

**Response 200**
```json
{
  "nodes": [
    { "id": "id", "name": "Qwen3", "type": "Concept" }
  ],
  "edges": [
    { "id": "id", "source": "id", "target": "id", "relation_type": "developed_by", "description": "..." }
  ]
}
```

---

### GET /graph/overview

Returns aggregated statistics for graph visualization bootstrap.

**Response 200**
```json
{
  "entity_count": 142,
  "relationship_count": 317,
  "entity_types": { "Concept": 60, "Person": 30, "Organization": 52 },
  "top_connected_entities": [
    { "id": "id", "name": "Qwen3", "degree": 14 }
  ]
}
```

---

### POST /graph/query (Cypher)

Execute a read-only Cypher query.

**Request:**
```json
{ "cypher": "MATCH (e:Entity {type: 'Person'}) RETURN e.name LIMIT 10" }
```

**Response 200**
```json
{ "columns": ["e.name"], "rows": [["John Doe"]] }
```

Write queries (CREATE, MERGE, DELETE) are rejected with HTTP 403.

---

## 5. Query (Graph RAG)

### POST /query

Run a Graph RAG query.

**Request:**
```json
{
  "query": "What are the key relationships between Qwen3 and its training data?",
  "strategy": "hybrid",
  "top_k": 5,
  "graph_depth": 2,
  "filters": {
    "document_ids": ["uuid"]
  },
  "stream": false
}
```

`strategy`: `"vector"` | `"graph"` | `"hybrid"` | `"multihop"`
`stream`: if `true`, use the streaming endpoint instead.

**Response 200 (non-streaming)**
```json
{
  "trace_id": "uuid",
  "answer": "Qwen3 was trained on...",
  "citations": [
    {
      "text": "Qwen3 training data includes...",
      "chunk_id": "uuid",
      "document_name": "qwen3_report.pdf",
      "page_number": 3,
      "chunk_index": 7
    }
  ],
  "total_latency_ms": 4200,
  "retrieval_latency_ms": 380,
  "generation_latency_ms": 3820
}
```

---

### GET /query/{trace_id}/trace

Retrieve the full execution trace.

**Response 200**
```json
{
  "id": "uuid",
  "query": "...",
  "retrieval_strategy": "hybrid",
  "retrieved_chunks": [
    { "chunk_id": "uuid", "text": "...", "score": 0.87, "document_name": "..." }
  ],
  "matched_entities": [
    { "id": "...", "name": "Qwen3", "type": "Concept", "match_score": 0.92 }
  ],
  "traversed_relationships": [
    { "from": "Qwen3", "relation": "developed_by", "to": "Alibaba" }
  ],
  "assembled_context": "...",
  "generated_answer": "...",
  "citations": [...],
  "token_usage": { "prompt_tokens": 1200, "completion_tokens": 280, "total_tokens": 1480 },
  "total_latency_ms": 4200
}
```

---

### POST /query/stream (Server-Sent Events)

Same request body as POST /query with `stream` ignored (always streams).

**Response:** `text/event-stream`

```
data: {"type":"chunk","content":"Qwen3 was"}
data: {"type":"chunk","content":" trained on"}
data: {"type":"done","trace_id":"uuid","citations":[...]}
```

---

## 6. Evaluation

### POST /evaluation/datasets

Create a new evaluation dataset.

**Request:**
```json
{
  "name": "Graph RAG Baseline v1",
  "description": "20-question synthetic dataset for retrieval regression.",
  "is_synthetic": true,
  "questions": [
    {
      "question": "...",
      "reference_answer": "...",
      "relevant_chunk_ids": ["uuid"],
      "relevant_entity_ids": ["neo4j-id"],
      "requires_multi_hop": false
    }
  ]
}
```

**Response 201** `{ "dataset_id": "uuid", "version": 1 }`

---

### GET /evaluation/datasets

List datasets. **Response 200** paginated list.

### GET /evaluation/datasets/{dataset_id}

Get a dataset with all questions.

---

### POST /evaluation/experiments

Run an evaluation experiment.

**Request:**
```json
{
  "name": "Hybrid vs Vector Baseline",
  "dataset_id": "uuid",
  "retrieval_strategy": "hybrid",
  "top_k": 5,
  "graph_depth": 2,
  "enable_tier2_metrics": false
}
```

**Response 202** `{ "experiment_id": "uuid", "status": "pending" }`

---

### GET /evaluation/experiments/{experiment_id}

Get experiment results.

**Response 200**
```json
{
  "id": "uuid",
  "name": "...",
  "status": "completed",
  "config_snapshot": { ... },
  "aggregate_metrics": {
    "hit_rate_at_5": 0.75,
    "mrr": 0.68,
    "ndcg_at_5": 0.72,
    "entity_precision": 0.81,
    "entity_recall": 0.74,
    "avg_latency_ms": 3800
  },
  "per_question_results": [ ... ],
  "created_at": "...",
  "completed_at": "..."
}
```

---

### GET /evaluation/experiments/{id}/export

Export results. **Query param:** `format=json` or `format=csv`. Returns file download.

---

### GET /evaluation/compare?experiment_a={id}&experiment_b={id}

Compare two experiments.

**Response 200**
```json
{
  "experiment_a": { "id": "...", "name": "..." },
  "experiment_b": { "id": "...", "name": "..." },
  "metrics_comparison": {
    "hit_rate_at_5": { "a": 0.65, "b": 0.75, "delta": 0.10, "winner": "b" },
    "mrr": { "a": 0.60, "b": 0.68, "delta": 0.08, "winner": "b" }
  }
}
```

---

## 7. Configuration

### GET /config/lmstudio/health

Check LM Studio connectivity and loaded models.

**Response 200**
```json
{
  "connected": true,
  "base_url": "http://localhost:1234/v1",
  "generation_model": { "id": "qwen3-8b", "available": true },
  "embedding_model": { "id": "qwen3-embedding-0.6b", "available": true }
}
```

### GET /config/system

Return non-sensitive system configuration (current settings, versions).

---

## 8. Error Format

All errors follow a consistent schema:

```json
{
  "error": "error_code_snake_case",
  "message": "Human-readable description.",
  "details": {}
}
```

| HTTP Status | Error Code | Meaning |
|-------------|------------|---------|
| 400 | `validation_error` | Invalid request body or parameters |
| 404 | `not_found` | Resource does not exist |
| 409 | `duplicate_document` | Content hash already exists |
| 413 | `file_too_large` | Exceeds 50MB limit |
| 415 | `unsupported_file_type` | File type not accepted |
| 403 | `forbidden_query` | Write Cypher blocked |
| 503 | `service_unavailable` | LM Studio or storage dependency down |
| 500 | `internal_error` | Unexpected server error |
