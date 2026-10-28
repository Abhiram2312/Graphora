# apps/backend/api/routers/health.py
"""Health check router.
Returns the health status of all backend dependencies.
For now each dependency is hard‑coded as healthy; real checks will be added later.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class DependenciesHealth(BaseModel):
    qdrant: str = "healthy"
    neo4j: str = "healthy"
    postgres: str = "healthy"
    redis: str = "healthy"
    lmstudio: str = "healthy"

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    dependencies: DependenciesHealth

@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Return overall health. In production this would query each service.
    """
    return HealthResponse()
