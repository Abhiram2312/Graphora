# DATA_MODEL.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. PostgreSQL Schema (Relational)

### documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen_random_uuid() | Document identifier |
| filename | TEXT | NOT NULL | Original filename or URL |
| source_type | TEXT | NOT NULL | 'pdf', 'txt', 'md', 'docx', 'url' |
| content_hash | TEXT | NOT NULL, UNIQUE | SHA-256 of raw content (deduplication) |
| status | TEXT | NOT NULL | 'pending', 'processing', 'completed', 'failed' |
| file_size_bytes | BIGINT | | File size |
| page_count | INT | | Populated for PDFs |
| metadata | JSONB | | Extracted title, author, etc. |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

### chunks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Chunk identifier |
| document_id | UUID | FK documents.id, NOT NULL | Parent document |
| chunk_index | INT | NOT NULL | Sequential index within document |
| text | TEXT | NOT NULL | Chunk content |
| char_start | INT | | Character offset start in document |
| char_end | INT | | Character offset end in document |
| page_number | INT | | For PDFs |
| token_count | INT | | Estimated token count |
| embedding_model | TEXT | NOT NULL | Model used to generate vector |
| qdrant_point_id | UUID | UNIQUE | Corresponding Qdrant point ID |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

### ingestion_jobs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Job identifier |
| document_id | UUID | FK documents.id | Associated document |
| status | TEXT | NOT NULL | 'queued', 'running', 'completed', 'failed' |
| current_step | TEXT | | 'parse', 'chunk', 'embed', 'extract', 'graph_write' |
| celery_task_id | TEXT | | Celery task identifier |
| steps_completed | JSONB | | Per-step duration and status |
| error_message | TEXT | | On failure |
| queued_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| started_at | TIMESTAMPTZ | | |
| completed_at | TIMESTAMPTZ | | |

### evaluation_datasets

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Dataset identifier |
| name | TEXT | NOT NULL | Human-readable name |
| description | TEXT | | |
| version | INT | NOT NULL, DEFAULT 1 | Incremented on update |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| is_synthetic | BOOLEAN | NOT NULL, DEFAULT FALSE | |

### evaluation_questions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Question identifier |
| dataset_id | UUID | FK evaluation_datasets.id, NOT NULL | |
| question | TEXT | NOT NULL | The query |
| reference_answer | TEXT | NOT NULL | Ground-truth answer |
| relevant_chunk_ids | UUID[] | | Expected relevant chunks (for Tier 1 metrics) |
| relevant_entity_ids | TEXT[] | | Expected entities (Neo4j node IDs) |
| requires_multi_hop | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| metadata | JSONB | | |

### experiments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Experiment identifier |
| name | TEXT | NOT NULL | Human-readable name |
| dataset_id | UUID | FK evaluation_datasets.id | |
| retrieval_strategy | TEXT | NOT NULL | 'vector', 'graph', 'hybrid', 'multihop' |
| config_snapshot | JSONB | NOT NULL | Full config at time of run (model IDs, K, depth, etc.) |
| status | TEXT | NOT NULL | 'pending', 'running', 'completed', 'failed' |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| completed_at | TIMESTAMPTZ | | |

### experiment_results

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| experiment_id | UUID | FK experiments.id | |
| question_id | UUID | FK evaluation_questions.id | |
| generated_answer | TEXT | | |
| retrieved_chunk_ids | UUID[] | | |
| retrieved_entity_ids | TEXT[] | | |
| trace_id | UUID | FK query_traces.id | |
| metrics | JSONB | | All computed metrics as key-value pairs |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

### query_traces

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Trace identifier |
| query | TEXT | NOT NULL | User query |
| retrieval_strategy | TEXT | NOT NULL | |
| retrieved_chunks | JSONB | | List of chunks with scores |
| matched_entities | JSONB | | List of matched graph entities |
| traversed_relationships | JSONB | | Graph edges traversed |
| assembled_context | TEXT | | Context sent to LLM |
| generated_answer | TEXT | | |
| citations | JSONB | | Per-claim source references |
| total_latency_ms | INT | | |
| retrieval_latency_ms | INT | | |
| generation_latency_ms | INT | | |
| token_usage | JSONB | | prompt_tokens, completion_tokens, total_tokens |
| model_id | TEXT | | Generation model used |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

## 2. Qdrant Schema (Vector Store)

### Collection: `graphora_chunks`

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Matches chunks.qdrant_point_id |
| vector | float[1024] | Qwen3-Embedding-0.6B embedding (dim verified at startup) |
| payload.document_id | UUID | For filtering by document |
| payload.chunk_id | UUID | PostgreSQL chunk ID |
| payload.chunk_index | int | Position in document |
| payload.text | string | Chunk text (for retrieval display) |
| payload.source_type | string | Document source type |
| payload.page_number | int | Nullable |

**Index configuration:** Payload indexes on `document_id` and `source_type` for metadata filtering. Distance metric: Cosine.

---

## 3. Neo4j Graph Schema

### Node Labels

#### `Entity`

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| id | STRING | Yes | UUID, unique |
| name | STRING | Yes | Canonical entity name |
| type | STRING | Yes | Entity type (e.g., 'Person', 'Organization', 'Concept', 'Location', 'Event') |
| description | STRING | | Brief description extracted from context |
| confidence | FLOAT | | Extraction confidence [0.0, 1.0] |
| aliases | LIST[STRING] | | Alternative names for the same entity |
| source_document_ids | LIST[STRING] | Yes | Document UUIDs this entity appears in |
| source_chunk_ids | LIST[STRING] | Yes | Chunk UUIDs this entity was extracted from |
| created_at | DATETIME | Yes | |
| updated_at | DATETIME | Yes | |

#### `Document` (graph mirror)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| id | STRING | Yes | Matches PostgreSQL documents.id |
| filename | STRING | Yes | |
| source_type | STRING | Yes | |

### Relationship Types

#### `RELATED_TO` (generic)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| id | STRING | Yes | UUID |
| relation_type | STRING | Yes | Extracted relation label (e.g., 'works_for', 'located_in') |
| description | STRING | | Natural language description |
| confidence | FLOAT | | [0.0, 1.0] |
| source_chunk_ids | LIST[STRING] | Yes | Provenance |
| created_at | DATETIME | Yes | |

#### `MENTIONED_IN`

Used between `Entity` and `Document` nodes. Property: `chunk_ids`.

### Indexes

```cypher
CREATE CONSTRAINT entity_id_unique FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE INDEX entity_name FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type FOR (e:Entity) ON (e.type);
CREATE INDEX document_id_unique FOR (d:Document) REQUIRE d.id IS UNIQUE;
```

### Entity Deduplication Strategy

Entities are deduplicated by normalized name within the same entity type:
1. Normalize: lowercase, strip punctuation, collapse whitespace.
2. Exact match on normalized name + type: merge (union source lists, update confidence).
3. No fuzzy matching in v1.0 (reserved for future improvement; see DECISIONS.md ADR-002).

---

## 4. Data Lifecycle

| Event | PostgreSQL | Qdrant | Neo4j |
|-------|-----------|--------|-------|
| Document ingested | Document + Chunks + Job rows created | Chunk vectors upserted | Entity/Relation nodes upserted |
| Document deleted | Document + Chunks deleted (cascade) | Points deleted by document_id filter | Nodes with no remaining sources deleted |
| Experiment run | Experiment + Results rows created | No change | No change |
| Evaluation dataset created/versioned | New dataset + question rows | No change | No change |

---

## 5. Schema Versioning

- PostgreSQL schema managed by Alembic. Each migration file has a `revision` ID and `down_revision` for rollback.
- Neo4j schema managed by a startup idempotent migration script that creates constraints and indexes if they do not exist.
- Qdrant collections are created at startup if they do not exist, with the configured vector size.
- **Breaking change rule:** Any change to vector dimensions, entity schema, or chunk schema that invalidates existing data requires a versioned migration and a documented re-ingestion path.
