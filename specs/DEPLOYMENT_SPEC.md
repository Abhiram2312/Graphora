# DEPLOYMENT_SPEC.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. Deployment Target

**v1.0 target:** Local development on a developer's machine using Docker Compose.

Cloud hosting is not configured in v1.0. The architecture is designed to support it without structural changes; cloud deployment documentation will be added in a future release.

---

## 2. Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | 24+ | Container runtime |
| Docker Compose | v2.x (bundled) | Service orchestration |
| Node.js | 20+ | Frontend dev server |
| pnpm | 9+ | Frontend package manager |
| LM Studio | Latest | Local model serving |
| Git | Any | Version control |

**For backend development outside Docker (optional):**
- Python 3.12+
- uv (Python package manager)

---

## 3. Repository Structure

```
graphora/
├── apps/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml        # uv-managed dependencies
│   │   └── ...
│   └── frontend/
│       ├── package.json
│       └── ...
├── specs/                         # SDD documents
├── docker-compose.yml             # Full local stack
├── docker-compose.test.yml        # CI-specific overrides
├── .env.example                   # Credential template
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── NOTICE
└── THIRD_PARTY_LICENSES.md
```

---

## 4. Docker Compose Configuration

### Services

```yaml
services:
  qdrant:
    image: qdrant/qdrant:v1.9.0
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5.18-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "neo4j", "status"]
      interval: 10s
      timeout: 10s
      retries: 10

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: graphora
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: graphora
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U graphora"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  api:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - LMSTUDIO_BASE_URL=${LMSTUDIO_BASE_URL}
      - LMSTUDIO_GENERATION_MODEL=${LMSTUDIO_GENERATION_MODEL}
      - LMSTUDIO_EMBEDDING_MODEL=${LMSTUDIO_EMBEDDING_MODEL}
      - LMSTUDIO_EMBEDDING_DIMENSIONS=${LMSTUDIO_EMBEDDING_DIMENSIONS}
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - DATABASE_URL=postgresql+asyncpg://graphora:${POSTGRES_PASSWORD}@postgres:5432/graphora
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - APP_ENV=development
    depends_on:
      qdrant:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads

volumes:
  qdrant_data:
  neo4j_data:
  postgres_data:
  redis_data:
```

---

## 5. First-Run Setup

```bash
# 1. Clone the repository
git clone https://github.com/<org>/graphora.git
cd graphora

# 2. Copy environment template
cp .env.example .env
# Edit .env with your values (at minimum: NEO4J_PASSWORD, POSTGRES_PASSWORD)

# 3. Start infrastructure services
docker compose up -d

# 4. Wait for all services to be healthy
docker compose ps

# 5. Run database migrations
docker compose exec api python -m alembic upgrade head

# 6. Start the frontend
cd apps/frontend
pnpm install
pnpm dev

# 7. Start LM Studio
# Load Qwen3 8B and Qwen3-Embedding-0.6B in LM Studio
# Ensure the server is running on http://localhost:1234

# 8. Verify the full stack
curl http://localhost:8000/api/v1/health
```

---

## 6. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LMSTUDIO_BASE_URL` | Yes | `http://localhost:1234/v1` | LM Studio server URL |
| `LMSTUDIO_GENERATION_MODEL` | Yes | `qwen3-8b` | Model identifier for generation + extraction |
| `LMSTUDIO_EMBEDDING_MODEL` | Yes | `qwen3-embedding-0.6b` | Embedding model identifier |
| `LMSTUDIO_EMBEDDING_DIMENSIONS` | Yes | `1024` | Embedding vector size |
| `LMSTUDIO_REQUEST_TIMEOUT` | No | `120` | Timeout in seconds for generation requests |
| `NEO4J_URI` | Yes | `bolt://localhost:7687` | Neo4j Bolt connection URI |
| `NEO4J_USER` | Yes | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | Yes | (none) | Neo4j password |
| `DATABASE_URL` | Yes | (none) | PostgreSQL async URL |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL |
| `QDRANT_HOST` | Yes | `localhost` | Qdrant hostname |
| `QDRANT_PORT` | Yes | `6333` | Qdrant HTTP port |
| `QDRANT_COLLECTION_NAME` | No | `graphora_chunks` | Vector collection name |
| `APP_ENV` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `UPLOAD_DIR` | No | `./uploads` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | No | `50` | Max file upload size |
| `CELERY_CONCURRENCY` | No | `2` | Celery worker concurrency |

---

## 7. Health Checks

`GET /api/v1/health` returns the health status of all dependencies. The response is used by:
- The frontend to show system status on the settings page.
- Docker Compose for the `api` service health check.
- CI smoke tests.

All five dependencies (qdrant, neo4j, postgres, redis, lmstudio) are checked independently. A degraded status is returned if any single dependency is unhealthy, with the specific unhealthy dependency identified.

---

## 8. Database Migrations

PostgreSQL migrations are managed by Alembic.

```bash
# Apply all pending migrations
docker compose exec api python -m alembic upgrade head

# Create a new migration (after changing SQLAlchemy models)
docker compose exec api python -m alembic revision --autogenerate -m "description"

# Roll back one migration
docker compose exec api python -m alembic downgrade -1
```

Neo4j schema (constraints and indexes) is applied by an idempotent startup script. No manual migration is needed for Neo4j in v1.0.

---

## 9. Backup Guidance

| Data | Backup method |
|------|--------------|
| PostgreSQL | `pg_dump graphora > backup.sql` inside the postgres container |
| Neo4j | Neo4j Community supports online backup via `neo4j-admin database dump` |
| Qdrant | Copy the `qdrant_data` Docker volume (stop Qdrant first) |
| Uploaded files | Copy the `./uploads` directory |

**Restore order (if rebuilding from scratch):** Start infrastructure, restore PostgreSQL, restore Neo4j, restore Qdrant, copy uploads, run `alembic upgrade head` (no-op if schema is current).

---

## 10. Logging

All backend services emit structured JSON logs to stdout.

Format per log line:
```json
{
  "timestamp": "2026-10-28T10:00:00.000Z",
  "level": "INFO",
  "service": "graphora-api",
  "request_id": "uuid",
  "event": "ingestion_job_completed",
  "document_id": "uuid",
  "duration_ms": 4200
}
```

In development (`APP_ENV=development`), logs are pretty-printed for readability.
In production, JSON logs are suitable for ingestion by any log aggregation system (Loki, Elasticsearch, CloudWatch).

---

## 11. Production Considerations (Future)

When cloud hosting is added:
- The API should bind to `0.0.0.0` with a reverse proxy (nginx/Caddy) in front.
- HTTPS must be terminated at the proxy.
- Neo4j, PostgreSQL, and Qdrant should run on persistent volumes with automated backups.
- LM Studio remains local; the application must support configuring an alternative inference endpoint (e.g., a dedicated GPU server).
- Secrets must use a secrets manager (e.g., AWS Secrets Manager, Doppler) rather than `.env` files.
- Rate limiting and authentication must be added before any public exposure.

These are not in scope for v1.0 but the architecture supports them without structural changes.
