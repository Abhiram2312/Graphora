# PROJECT_VISION.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## Product Name

**Graphora** — Open-Source Graph RAG and Evaluation Platform

---

## Vision Statement

Graphora gives developers a single, locally-run workspace to build knowledge graphs from their documents, run Graph RAG pipelines against locally hosted language models, and systematically evaluate retrieval and generation quality — with full transparency into every step of the process.

---

## Goals

### Primary

1. **Reproducible Graph RAG** — Build, query, and re-run knowledge-graph pipelines against the same document corpus with identical configuration, producing comparable results across experiments.
2. **Local-first inference** — All LLM inference (generation, embeddings, entity extraction) runs through LM Studio. No document or query data leaves the local environment unless explicitly configured.
3. **Structured evaluation** — Measure retrieval and generation quality with deterministic and judge-based metrics. Compare Graph RAG against vector RAG. Track experiment history.
4. **Full pipeline transparency** — Every query exposes an inspectable execution trace: chunks retrieved, graph nodes matched, context sent to the model, generated answer, citations, and per-step latency.
5. **Useful open-source reference** — A well-engineered, documented reference implementation that developers can fork, extend, and deploy.

### Secondary

- Interactive graph visualization for exploring entity and relationship structure.
- Side-by-side comparison of retrieval strategies within the same experiment.
- CI-compatible evaluation fixtures for automated regression detection.

---

## Scope

### In Scope (v1.0 release)

- Document ingestion: PDF, plain text (.txt), Markdown (.md), Word (.docx), and web URLs via scraping
- Chunking, embedding, entity extraction, relationship extraction
- Vector storage (Qdrant) and graph storage (Neo4j Community)
- Graph RAG retrieval strategies: vector similarity, graph traversal, hybrid, multi-hop
- Answer generation via LM Studio (Qwen3 8B)
- Execution trace and provenance for every query
- Evaluation: Tier 1 deterministic metrics, Tier 2 RAGAS-based metrics, Tier 3 graph-specific metrics
- Experiment management and comparison dashboards
- Interactive knowledge graph explorer (D3.js force-directed)
- 11-page frontend with Anime.js animations
- GitHub Actions CI with evaluation regression
- Docker Compose for local development
- Open-source release with README, contribution guide, code of conduct, security policy

### Explicitly Out of Scope (v1.0)

- WhatsApp and email notifications (adapter interface reserved, not implemented)
- Multi-user authentication and RBAC
- Cloud hosting configuration (local development only at release)
- Model fine-tuning or training
- External paid LLM API integrations
- Mobile native applications

---

## Target Users

**Primary:** Developers building, evaluating, or researching Graph RAG systems who want a complete, locally reproducible environment.

**Secondary:** Researchers comparing retrieval strategies; engineering teams using this as a foundation for production Graph RAG systems.

---

## Open-Source Commitment

- Apache License 2.0 for all application code
- Third-party dependencies documented in `NOTICE` and `THIRD_PARTY_LICENSES.md`
- No mandatory proprietary dependencies
- No phone-home telemetry or analytics
- Core features fully functional without any external services
- Neo4j Community Edition used as a runtime dependency under its own GPL-3.0 license; the application code does not incorporate Neo4j source and communicates with it solely over the network Bolt protocol
