# apps/backend/api/routers/evaluation.py
"""Evaluation router (stub).
Provides minimal endpoints for dataset and experiment management.
Later phases will implement full evaluation pipeline.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

router = APIRouter()

# ---- In‑memory placeholder stores ---------------------------------------
_fake_datasets: dict[str, dict] = {}
_fake_experiments: dict[str, dict] = {}

# ---- Pydantic models ---------------------------------------------------
class DatasetCreate(BaseModel):
    name: str
    description: str | None = None
    is_synthetic: bool = False
    # questions omitted for stub

class DatasetResponse(BaseModel):
    dataset_id: str
    version: int = 1
    name: str
    description: str | None = None
    created_at: datetime

class ExperimentCreate(BaseModel):
    name: str
    dataset_id: str
    retrieval_strategy: str = "hybrid"
    top_k: int = 5
    graph_depth: int = 2
    enable_tier2_metrics: bool = False

class ExperimentResponse(BaseModel):
    experiment_id: str
    status: str = "pending"
    name: str
    dataset_id: str
    created_at: datetime
    completed_at: datetime | None = None

# ---- Endpoints ----------------------------------------------------------
@router.post("/evaluation/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(payload: DatasetCreate):
    ds_id = str(uuid.uuid4())
    now = datetime.utcnow()
    _fake_datasets[ds_id] = {
        "id": ds_id,
        "name": payload.name,
        "description": payload.description,
        "created_at": now,
        "version": 1,
    }
    return DatasetResponse(
        dataset_id=ds_id,
        version=1,
        name=payload.name,
        description=payload.description,
        created_at=now,
    )

@router.get("/evaluation/datasets", response_model=list[DatasetResponse])
async def list_datasets():
    return [
        DatasetResponse(
            dataset_id=ds["id"],
            version=ds.get("version", 1),
            name=ds["name"],
            description=ds.get("description"),
            created_at=ds["created_at"],
        )
        for ds in _fake_datasets.values()
    ]

@router.post("/evaluation/experiments", response_model=ExperimentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_experiment(payload: ExperimentCreate):
    if payload.dataset_id not in _fake_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    exp_id = str(uuid.uuid4())
    now = datetime.utcnow()
    _fake_experiments[exp_id] = {
        "id": exp_id,
        "name": payload.name,
        "dataset_id": payload.dataset_id,
        "status": "pending",
        "created_at": now,
        "completed_at": None,
    }
    return ExperimentResponse(
        experiment_id=exp_id,
        status="pending",
        name=payload.name,
        dataset_id=payload.dataset_id,
        created_at=now,
    )

@router.get("/evaluation/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str):
    exp = _fake_experiments.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentResponse(
        experiment_id=exp["id"],
        status=exp["status"],
        name=exp["name"],
        dataset_id=exp["dataset_id"],
        created_at=exp["created_at"],
        completed_at=exp["completed_at"],
    )
