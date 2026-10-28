# apps/backend/api/routers/query.py
"""Graph RAG query router (stub).
Provides a simple endpoint that pretends to run a retrieval+generation pipeline
and returns a deterministic response with a trace_id.
Later phases will replace the stub with real retrieval, LM Studio calls, and
trace building.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., description="User question")
    strategy: str = Field("hybrid", description="vector | graph | hybrid | multihop")
    top_k: int = Field(5, ge=1)
    graph_depth: int = Field(2, ge=1)
    filters: dict | None = None
    stream: bool = False

class Citation(BaseModel):
    text: str
    chunk_id: str
    document_name: str
    page_number: int | None = None
    chunk_index: int | None = None

class QueryResponse(BaseModel):
    trace_id: str
    answer: str
    citations: list[Citation]
    total_latency_ms: int
    retrieval_latency_ms: int
    generation_latency_ms: int

@router.post("/query", response_model=QueryResponse)
async def run_query(req: QueryRequest):
    # Deterministic placeholder – echo the query and dummy citation.
    trace_id = str(uuid.uuid4())
    answer = f"This is a placeholder answer for: {req.query}"
    citation = Citation(
        text="Placeholder citation text",
        chunk_id=str(uuid.uuid4()),
        document_name="demo.pdf",
        page_number=1,
        chunk_index=0,
    )
    now = datetime.utcnow()
    # In a real implementation these latencies would be measured; we return static values.
    return QueryResponse(
        trace_id=trace_id,
        answer=answer,
        citations=[citation],
        total_latency_ms=1234,
        retrieval_latency_ms=567,
        generation_latency_ms=667,
    )

@router.get("/query/{trace_id}/trace")
async def get_trace(trace_id: str):
    # Stub – return minimal trace information.
    return {
        "id": trace_id,
        "query": "placeholder",
        "retrieval_strategy": "hybrid",
        "retrieved_chunks": [],
        "matched_entities": [],
        "generated_answer": "placeholder",
        "citations": [],
        "latency_ms": 0,
    }
