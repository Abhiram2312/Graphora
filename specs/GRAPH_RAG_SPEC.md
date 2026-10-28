# GRAPH_RAG_SPEC.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. Conceptual Pipeline

```
Document(s)
    │
    ├─ Parse (PDF/TXT/MD/DOCX/URL)
    ├─ Clean and normalize text
    ├─ Chunk (fixed-size with overlap)
    ├─ Embed chunks (Qwen3-Embedding-0.6B)
    ├─ Write vectors → Qdrant
    ├─ Extract entities + relations (Qwen3 8B, JSON-mode)
    ├─ Deduplicate and resolve entities
    └─ Write graph → Neo4j

                    ┌─────────────────────────────┐
User query ────────▶│     Graph RAG Engine         │
                    │                             │
                    │  1. Query analysis           │
                    │  2. Entity extraction from  │
                    │     query                   │
                    │  3. Parallel retrieval      │
                    │     a. Vector: Qdrant       │
                    │     b. Graph: Neo4j Cypher  │
                    │  4. Merge and rank results  │
                    │  5. Assemble context with   │
                    │     provenance              │
                    │  6. Generate via Qwen3 8B   │
                    │  7. Validate citations       │
                    │  8. Build execution trace   │
                    └─────────────────────────────┘
                                │
                         Answer + Trace
```

---

## 2. Document Processing

### 2.1 Supported Parsers

| Source | Library | Output |
|--------|---------|--------|
| PDF | `pypdf2` or `pdfplumber` | Text per page |
| Plain text | Built-in | Full text |
| Markdown | `markdown-it-py` (strip to plain text) | Plain text |
| Word (.docx) | `python-docx` | Text per paragraph |
| Web URL | `httpx` + `beautifulsoup4` (body text only) | Plain text |

**Post-parse cleaning:** Strip excessive whitespace, normalize Unicode, remove headers/footers (heuristic for PDFs), detect and skip empty pages.

### 2.2 Chunking

Default strategy: **fixed-size token-aware chunking with overlap.**

| Parameter | Default | Configurable |
|-----------|---------|-------------|
| chunk_size | 512 tokens | Yes (per request) |
| chunk_overlap | 50 tokens | Yes (per request) |
| separator | Paragraph boundary preferred | No |

Token count is estimated using the tokenizer for Qwen3 8B (or a fast tiktoken approximation). Chunks respect sentence and paragraph boundaries where possible; they do not split in the middle of a sentence unless the sentence exceeds `chunk_size`.

---

## 3. Embedding

**Model:** Qwen3-Embedding-0.6B (served via LM Studio)
**Dimension:** 1024 (verified at startup via a test embedding; startup fails if dimension mismatch with Qdrant collection)
**Distance metric:** Cosine

Embeddings are generated in batches (batch size: 32 by default, configurable). The LM Studio embedding endpoint is called as: `POST /v1/embeddings` with the standard OpenAI request format.

---

## 4. Entity and Relationship Extraction

### 4.1 Model and Prompt Design

**Model:** Qwen3 8B via LM Studio (`/v1/chat/completions`, JSON mode)

**System prompt (extraction task):**
```
You are a knowledge graph extraction assistant. Extract all entities and relationships from the provided text.

Output valid JSON only. Do not include any explanation outside the JSON object.

Schema:
{
  "entities": [
    {
      "name": "string",
      "type": "Person | Organization | Concept | Location | Event | Product | Other",
      "description": "1-2 sentence description",
      "confidence": 0.0-1.0
    }
  ],
  "relationships": [
    {
      "source": "entity name (must match an entity above)",
      "target": "entity name (must match an entity above)",
      "relation_type": "snake_case_verb_phrase",
      "description": "1 sentence description",
      "confidence": 0.0-1.0
    }
  ]
}
```

**User message:** `Extract entities and relationships from the following text:\n\n<CHUNK_TEXT>`

Document content is delimited and never mixed with system instructions (prompt injection mitigation).

### 4.2 JSON Parsing and Validation

Extraction responses are validated against the schema above using Pydantic. Invalid or missing fields default to safe values:
- Missing `confidence`: defaults to `0.5`
- Missing `description`: defaults to `""`
- Relationship with a source or target not in `entities`: discarded with a warning log

Any non-JSON text in the response is discarded. If JSON parsing fails entirely, the chunk is marked with `extraction_status: failed` and processing continues.

### 4.3 Entity Deduplication

Within a single ingestion job:
1. Normalize entity names (lowercase, strip punctuation).
2. Exact match on normalized name + type across all chunks.
3. Merge duplicates: union `source_chunk_ids`, keep the highest `confidence`, concatenate `descriptions` (truncated).

Across documents (incremental graph updates):
1. Same normalization and exact match against existing Neo4j entities.
2. `MERGE` on `(e:Entity {name: $normalized_name, type: $type})`.
3. On match: `SET e.source_document_ids = e.source_document_ids + $new_doc_id` (deduplicated), update `updated_at`.

No fuzzy matching in v1.0.

---

## 5. Retrieval Strategies

All strategies accept these shared parameters:
- `query`: string
- `top_k`: int (default 5)
- `filters`: optional `{ document_ids: [], source_types: [] }`

### 5.1 Vector Similarity

1. Embed the query with Qwen3-Embedding-0.6B.
2. Search Qdrant with cosine similarity.
3. Apply metadata filters if provided.
4. Return top-K chunks with scores.

### 5.2 Graph Traversal

1. Extract entities from the query (Qwen3 8B, lightweight extraction prompt, max 5 entities).
2. For each extracted entity, search Neo4j for matching `Entity` nodes (full-text search on `name`).
3. For each matched node, execute a Cypher traversal up to `graph_depth` hops:
   ```cypher
   MATCH path = (e:Entity {id: $entity_id})-[*1..$depth]-(neighbor:Entity)
   RETURN neighbor, relationships(path)
   ORDER BY length(path)
   LIMIT $top_k
   ```
4. Collect all traversed nodes and edges.
5. For each traversed entity, retrieve the corresponding chunks from PostgreSQL (via `source_chunk_ids`).
6. Return chunks with graph path provenance.

### 5.3 Hybrid (Vector + Graph)

1. Run vector retrieval and graph traversal in parallel.
2. Combine results using **Reciprocal Rank Fusion (RRF):**
   ```
   score(d) = sum over strategies: 1 / (k + rank_in_strategy(d))
   ```
   Default `k = 60`.
3. Deduplicate by chunk ID; keep highest combined score.
4. Return top-K results with scores from each contributing strategy.

### 5.4 Multi-Hop Graph

Like graph traversal but with `graph_depth` defaulting to 2 (configurable up to 4). Multi-hop queries are identified when the query contains comparison, causation, or transitivity language patterns (heuristic detection; exact NLP classification not required in v1.0).

---

## 6. Context Assembly

After retrieval, context is assembled in a deterministic order:

1. Sort retrieved chunks by final score (descending).
2. Prepend each chunk with its provenance header:
   ```
   [Source: {document_name}, page {page_number}, chunk {chunk_index}]
   {chunk_text}
   ```
3. Concatenate until the context window budget is reached.
4. Context window budget: `model_context_window - prompt_overhead - max_completion_tokens`.
   - For Qwen3 8B: model context window 32,768 tokens; reserved for prompt overhead 512; max completion 1,024; usable context budget ~31,232 tokens.
5. If retrieved context exceeds budget, truncate lowest-scoring chunks.

---

## 7. Generation

**Model:** Qwen3 8B via LM Studio
**Endpoint:** `POST /v1/chat/completions`

**System prompt (generation task):**
```
You are a research assistant with access to retrieved information. Answer the user's question using only the provided context. If the context does not contain enough information to answer the question, say so explicitly. Do not fabricate information.

For each claim in your answer, provide an inline citation in the format [Source: document_name, chunk N].
```

**User message:**
```
Context:
{assembled_context}

Question: {user_query}
```

**Parameters:**
- `temperature`: 0.1 (low, for factual consistency)
- `max_tokens`: 1024
- `stream`: true (streaming to frontend via SSE)

---

## 8. Citation Validation

After generation:
1. Parse inline citations from the generated answer (regex: `\[Source: .+?, chunk \d+\]`).
2. For each parsed citation, verify the referenced document name and chunk index exist in the retrieved chunks.
3. Citations that cannot be matched are flagged as `unverified` in the trace (not removed from the answer; flagged for the user).
4. `provenance_completeness` = verified citations / total citations (Tier 3 metric).

---

## 9. Execution Trace

Every query builds a `QueryTrace` object incrementally:

| Field | Populated at |
|-------|-------------|
| `query` | Request received |
| `retrieval_strategy` | Request received |
| `retrieval_start_ms` | Before retrieval |
| `retrieved_chunks` | After retrieval |
| `matched_entities` | After entity extraction from query |
| `traversed_relationships` | After graph traversal (if applicable) |
| `retrieval_latency_ms` | After retrieval completes |
| `assembled_context` | After context assembly |
| `generation_start_ms` | Before LM Studio call |
| `generated_answer` | After generation completes |
| `token_usage` | From LM Studio response metadata |
| `generation_latency_ms` | After generation completes |
| `citations` | After citation validation |
| `total_latency_ms` | Before storing trace |

The trace is stored in PostgreSQL and returned with the response as a `trace_id`. Full trace is available at `GET /query/{trace_id}/trace`.

---

## 10. LM Studio Connector

The `LMStudioConnector` is the sole point of interaction with LM Studio.

```
LMStudioConnector
├── generate(messages, stream, max_tokens, temperature) -> AsyncGenerator[str] | str
├── embed(texts: list[str]) -> list[list[float]]
├── extract_entities(chunk_text: str) -> ExtractionResult
└── health() -> LMStudioHealthStatus
```

**Error handling:**
- `ConnectError`: LM Studio server unreachable. Raises `LMStudioUnavailableError` with a human-readable message.
- `httpx.TimeoutException`: Configurable timeout (default 120s for generation, 30s for embeddings). Raises `LMStudioTimeoutError`.
- Non-200 response from LM Studio: Raises `LMStudioAPIError` with status code and response body.
- All errors are logged at ERROR level with request context (model, task type, truncated prompt).

**No fallback to external APIs.** If LM Studio is unavailable, the operation fails with a clear error. There is no silent fallback.
