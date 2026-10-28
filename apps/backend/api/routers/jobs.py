# apps/backend/api/routers/jobs.py
"""Jobs router (stub).
Provides an endpoint to poll the status of ingestion or other background jobs.
Currently uses an in‑memory placeholder store populated by the document router.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

router = APIRouter()

# Simple placeholder store – jobs are added by the document router when ingest is requested.
_fake_jobs: dict[str, dict] = {}

class StepInfo(BaseModel):
    status: str = "pending"  # pending | running | completed | failed
    duration_ms: int | None = None

class JobStatusResponse(BaseModel):
    id: str
    document_id: str | None = None
    status: str = "queued"  # queued | running | completed | failed
    current_step: str | None = None
    steps_completed: dict[str, StepInfo] = {}
    error_message: str | None = None
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    job = _fake_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Convert steps dict to StepInfo models
    steps = {name: StepInfo(**info) for name, info in job.get("steps_completed", {}).items()}
    return JobStatusResponse(
        id=job_id,
        document_id=job.get("document_id"),
        status=job.get("status", "queued"),
        current_step=job.get("current_step"),
        steps_completed=steps,
        error_message=job.get("error_message"),
        queued_at=job["queued_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
    )

# Helper function for other routers to create a new job entry.
def create_job(document_id: str | None = None) -> str:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    _fake_jobs[job_id] = {
        "document_id": document_id,
        "status": "queued",
        "current_step": None,
        "steps_completed": {},
        "error_message": None,
        "queued_at": now,
        "started_at": None,
        "completed_at": None,
    }
    return job_id
