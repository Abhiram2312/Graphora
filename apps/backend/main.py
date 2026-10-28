# apps/backend/main.py
"""FastAPI application factory.
Includes lifespan events to connect/disconnect DBs, and mounts the API routers.
"""

import logging
from fastapi import FastAPI
from structlog import get_logger

from .config import settings
from .api.routers import health, documents, graph, query, evaluation, jobs

logger = get_logger()

app = FastAPI(
    title="Graphora Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register routers (prefix /api/v1)
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    logger.info("Starting Graphora backend", env=settings.APP_ENV)
    # Placeholder: initialize DB connections, health checks, etc.
    # Real implementations will be added later.

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down Graphora backend")
    # Placeholder: close DB connections.
