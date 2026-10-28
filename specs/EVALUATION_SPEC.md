# EVALUATION_SPEC.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. Evaluation Philosophy

- Tier 1 (deterministic) metrics are the primary signals. They have no external dependencies and are exact.
- Tier 2 (RAGAS-based LLM-judge) metrics are supplemental. They require a configured judge model and are recorded as subjective signals, not ground truth.
- Tier 3 (graph-specific) metrics measure capabilities unique to Graph RAG.
- No evaluation result is ever fabricated or estimated without real computation.
- Every experiment stores a complete configuration snapshot so results are reproducible.

---

## 2. Evaluation Dataset Schema

An evaluation dataset contains:
- A set of `EvaluationQuestion` records (see DATA_MODEL.md).
- Each question has: `question`, `reference_answer`, `relevant_chunk_ids`, `relevant_entity_ids`, `requires_multi_hop`.

### Dataset Versioning

Editing a dataset creates a new version (incremented `version` field); the original is not overwritten. Experiments reference the dataset by ID + version.

### Synthetic CI Dataset

A 20-question synthetic dataset (`fixtures/eval_dataset_synthetic.json`) is committed to the repository. It:
- Uses chunk IDs from a small fixture document corpus (also committed as plain text files).
- Has deterministic expected outputs for all Tier 1 metrics.
- Does not require any real model or real ingestion to compute Tier 1 metrics.

---

## 3. Tier 1: Deterministic Metrics

These metrics require only ground-truth relevant chunk IDs and the list of retrieved chunk IDs. No model is needed.

### 3.1 Hit Rate @ K

```
HitRate@K = (number of questions where at least one relevant chunk appears in top-K) / total questions
```

**Input:** For each question, list of retrieved chunk IDs (ordered by score), list of ground-truth relevant chunk IDs.
**K values computed:** 1, 3, 5, 10.

---

### 3.2 Mean Reciprocal Rank (MRR)

```
MRR = (1/|Q|) * sum_q (1 / rank_of_first_relevant_chunk_q)
```

If no relevant chunk appears in the retrieved list, the reciprocal rank for that question is 0.

---

### 3.3 NDCG @ K

```
DCG@K = sum_{i=1}^{K} (rel_i / log2(i+1))
IDCG@K = DCG@K for ideal ordering
NDCG@K = DCG@K / IDCG@K
```

Binary relevance: `rel_i = 1` if chunk at rank `i` is in ground-truth relevant set, else 0.
**K values computed:** 5, 10.

---

### 3.4 Entity Extraction Precision and Recall

Computed per document (requires annotated entity lists in evaluation questions).

```
Precision = |extracted_entities ∩ ground_truth_entities| / |extracted_entities|
Recall    = |extracted_entities ∩ ground_truth_entities| / |ground_truth_entities|
F1        = 2 * P * R / (P + R)
```

Entity matching: exact match on normalized name + type.

---

### 3.5 End-to-End Latency

Recorded per query from the `QueryTrace`:
- `total_latency_ms`
- `retrieval_latency_ms`
- `generation_latency_ms`

Reported as: mean, median, p90, p99 over the experiment dataset.

---

### 3.6 Token Usage

From LM Studio response metadata per query:
- `prompt_tokens`: mean over dataset
- `completion_tokens`: mean over dataset
- `total_tokens`: mean over dataset

---

## 4. Tier 2: RAGAS-Based Metrics

These metrics use an LLM judge. They are only computed when `enable_tier2_metrics: true` is set in the experiment config AND a judge model is configured in settings.

**Judge model default:** Qwen3 8B (same model as generation). This is documented as a limitation: the judge is not independent. Users should be aware that self-evaluation introduces bias.

**RAGAS version pinned:** `ragas==0.2.x` (pinned in `requirements.txt`). The exact version and judge model identifier are stored in every experiment config snapshot.

### 4.1 Faithfulness

Measures: does the generated answer contain claims that are supported by the retrieved context?

**RAGAS implementation:** `Faithfulness` metric from `ragas.metrics`.
**Input:** question, answer, retrieved_contexts (list of chunk texts).
**Output:** float [0.0, 1.0]. Higher is better (1.0 = all claims supported).
**Limitation recorded:** LLM-judge score, not ground truth. Stored with judge model ID.

### 4.2 Answer Relevance

Measures: is the generated answer relevant to the question?

**RAGAS implementation:** `AnswerRelevancy` metric.
**Input:** question, answer.
**Output:** float [0.0, 1.0].

### 4.3 Answer Correctness

Measures: how correct is the generated answer compared to the reference answer?

**RAGAS implementation:** `AnswerCorrectness` metric.
**Input:** question, answer, reference_answer.
**Output:** float [0.0, 1.0].

### 4.4 Context Relevance

Measures: how relevant is the retrieved context to the question?

**RAGAS implementation:** `ContextRelevancy` metric.
**Input:** question, retrieved_contexts.
**Output:** float [0.0, 1.0].

---

## 5. Tier 3: Graph-Specific Metrics

### 5.1 Multi-Hop Retrieval Success Rate

```
MultiHopSuccess = (questions where requires_multi_hop=True AND relevant entity in retrieved context) / total multi-hop questions
```

A question is considered "succeeded" if at least one entity from `relevant_entity_ids` appears in `retrieved_entity_ids` from the query trace.

### 5.2 Graph Evidence Coverage

```
GraphEvidenceCoverage = (answer claims with at least one citation linked to a graph entity) / total answer claims
```

Claims are sentences in the answer. "Linked to a graph entity" means the citation's chunk was retrieved via graph traversal (recorded in trace `traversed_relationships`).

### 5.3 Provenance Completeness

```
ProvenanceCompleteness = verified_citations / total_citations
```

A citation is "verified" if the referenced document name and chunk index match a chunk in the retrieved set. Computed during citation validation (see GRAPH_RAG_SPEC.md Section 8).

### 5.4 Relationship Extraction F1

Requires annotated relationship triples (optional; only computed if ground-truth relations are provided in the evaluation question).

```
Relation triple = (source_entity_name, relation_type, target_entity_name)
Precision = |extracted_triples ∩ ground_truth_triples| / |extracted_triples|
Recall    = |extracted_triples ∩ ground_truth_triples| / |ground_truth_triples|
F1        = 2 * P * R / (P + R)
```

Matching: exact on normalized source name, exact on target name, exact on relation type.

---

## 6. Experiment Execution Flow

```
POST /evaluation/experiments
        │
        ▼
Create Experiment record (status: pending)
        │
        ▼
For each question in dataset:
    │
    ├── POST /query (with experiment config)
    ├── Retrieve QueryTrace
    ├── Compute Tier 1 metrics from trace + ground truth
    ├── Compute Tier 3 metrics from trace
    ├── (If enabled) Compute Tier 2 metrics via RAGAS
    └── Store ExperimentResult
        │
        ▼
Aggregate metrics across all questions
        │
        ▼
Update Experiment status to completed
        │
        ▼
Store aggregate_metrics in Experiment record
```

All steps run as a Celery task. The experiment status is pollable via `GET /evaluation/experiments/{id}`.

---

## 7. CI Evaluation Regression

The GitHub Actions `evaluation-regression` workflow:

1. Starts a PostgreSQL and Qdrant container (mocked data pre-seeded from fixtures).
2. Loads the synthetic 20-question dataset from `tests/fixtures/eval_dataset_synthetic.json`.
3. Uses a `MockLMStudioClient` that returns deterministic responses from `tests/fixtures/mock_responses/`.
4. Runs the full evaluation pipeline.
5. Asserts that Tier 1 metrics meet the thresholds defined in `tests/fixtures/eval_thresholds.json`.
6. Fails the workflow if any threshold is breached.

**Threshold file format (`eval_thresholds.json`):**
```json
{
  "hit_rate_at_5": { "min": 0.70 },
  "mrr": { "min": 0.60 },
  "ndcg_at_5": { "min": 0.65 }
}
```

These thresholds are set conservatively for mock responses and updated as the system matures.

**No real LM Studio instance is required or contacted in CI.** This is enforced by an environment variable guard: if `LMSTUDIO_BASE_URL` is not set, the mock client is used automatically.

---

## 8. Evaluation Report Format

### JSON export

Full experiment record including config snapshot, aggregate metrics, and per-question results.

### CSV export

One row per question with columns: `question_id`, `question`, `generated_answer`, `reference_answer`, and one column per metric.

### Comparison report

When comparing two experiments, the output includes:
- Side-by-side metric table with delta values.
- A `winner` field per metric (experiment A, B, or `tie` if delta < 0.01).
- Questions where the two experiments disagreed significantly (answer correctness delta > 0.2).

---

## 9. Limitations and Honest Disclosures

| Limitation | Disclosure |
|-----------|-----------|
| RAGAS LLM-judge self-evaluation | When Qwen3 8B judges its own outputs, bias is expected. Results are labeled "self-evaluated" in all reports. |
| Entity extraction matching is exact-only | Fuzzy matching would improve recall; deferred to v1.1. |
| Synthetic CI dataset is artificial | Thresholds set on synthetic data may not reflect real-world performance. Real evaluation should be run separately with real data. |
| Token usage from LM Studio | `prompt_tokens` and `completion_tokens` are provided by LM Studio's response; accuracy depends on the model's tokenizer reporting. |
| Multi-hop success is binary | A partial multi-hop retrieval (some but not all hops) is not distinguished from complete failure in v1.0. |
