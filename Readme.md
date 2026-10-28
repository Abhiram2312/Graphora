# Graph RAG

An open-source Graph Retrieval-Augmented Generation (Graph RAG) system that combines knowledge graphs, vector search, and local Large Language Models (LLMs) to deliver context-aware, traceable answers.

## Overview

Graph RAG enhances traditional RAG by connecting information through relationships in a knowledge graph. This enables the system to retrieve relevant context using both semantic similarity and entity relationships.

The project aims to provide a modular platform for building, testing, evaluating, and experimenting with Graph RAG pipelines using open-source technologies and locally hosted models.

## Key Features

- **Graph-based retrieval** — Retrieve information using entities and their relationships.
- **Vector search** — Find semantically relevant document chunks.
- **Local LLM inference** — Run models locally using LM Studio.
- **Evaluation framework** — Measure retrieval quality and answer generation performance.
- **Configurable models** — Switch LLMs and embedding models without changing core application logic.
- **Interactive web interface** — A modern UI with smooth animations and responsive layouts.
- **Open source** — Designed to be extensible and community-friendly.

## Initial Model Configuration

| Component | Model | Purpose |
|---|---|---|
| LLM | Qwen3 8B Instruct | Answer generation and reasoning |
| Embeddings | Qwen3-Embedding-0.6B | Semantic vector representations |
| Inference | LM Studio | Local model serving |

Additional reranking models and alternative model configurations can be introduced as the project evolves.

## Technology Stack

The final technology stack will be defined through Spec-Driven Development (SDD).

Planned components include:

- **LLM Runtime:** LM Studio
- **Language Models:** Qwen3 family
- **Retrieval:** Graph-based retrieval and vector search
- **Graph Database:** Neo4j Community Edition (initial candidate)
- **Evaluation:** RAG evaluation metrics and custom benchmarks
- **Frontend:** Modern, responsive web interface with animations
- **CI/CD:** GitHub Actions

Specific technologies and integrations will be finalized before implementation.

## Evaluation

The system will be evaluated using metrics such as:

- Faithfulness
- Answer relevancy
- Context precision
- Context recall
- Retrieval quality
- Response latency

The evaluation framework will help compare model configurations and identify weaknesses in retrieval and answer generation.

## Development Approach

This project follows **Spec-Driven Development (SDD)**.

Development will proceed through the following stages:

1. Define the project mission, requirements, and architecture.
2. Create and review technical specifications.
3. Validate model compatibility and local resource requirements.
4. Implement approved components incrementally.
5. Run automated tests and RAG evaluations.
6. Document results and refine the system.

Implementation will begin only after the relevant specifications and plans have been reviewed and approved.

## Hardware

Initial development target:

- **GPU:** NVIDIA RTX 4070 Ti, 12 GB VRAM
- **RAM:** 64 GB
- **Local inference:** LM Studio

Model quantization, context length, and GPU memory usage will be optimized for the available hardware.

## Licensing

The application is intended to use the **Apache License 2.0**, subject to verification of third-party dependencies and their respective licenses.

Neo4j Community Edition and all other dependencies must retain their applicable license notices and comply with their licensing requirements.

## Project Status

**Status:** Planning and specification

The initial architecture, model configuration, evaluation strategy, and implementation plan will be established before development begins.

## Contributing

Contributions are welcome. Please review the project specifications and proposed changes before implementing significant features.

## License

The project is intended to be licensed under Apache License 2.0. See the `LICENSE` file once the license has been finalized and added to the repository.