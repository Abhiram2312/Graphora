# apps/backend/api/routers/documents.py
"""Document management router (stub implementations).
In Phase 3 these will be wired to actual ingestion pipelines, but for now we
return deterministic placeholder responses that satisfy the OpenAPI spec.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

router = APIRouter()

# ---- Pydantic models ----------------------------------------------------
class DocumentBase(BaseModel):
    filename: str
    source_type: str = Field(..., description="pdf | txt | md | docx | url")

class DocumentCreateResponse(BaseModel):
    job_id: str
    document_id: str
    status: str = "queued"
    message: str = "Ingestion job queued."

class DocumentInfo(BaseModel):
    id: str
    filename: str
    source_type: str
    status: str
    page_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime

class DocumentListResponse(BaseModel):
    items: list[DocumentInfo]
    total: int
    page: int = 1
    page_size: int = 20

# In‑memory placeholder store (will be replaced by DB in later phases)
_fake_store: dict[str, DocumentInfo] = {}

# ---- Endpoints ----------------------------------------------------------
@router.post("/documents/ingest", response_model=DocumentCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document():
    """Accept a multipart file upload – stub returns placeholder IDs.
    The actual file handling will be added in Phase 3.
    """
    doc_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    fake_store[doc_id] = DocumentInfo(
        id=doc_id,
        filename="placeholder.pdf",
        source_type="pdf",
        status="queued",
        page_count=None,
        chunk_count=None,
        created_at=now,
    )
    return DocumentCreateResponse(job_id=job_id, document_id=doc_id)

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(page: int = 1, page_size: int = 20, status: str | None = None):
    docs = list(fake_store.values())
    start = (page - 1) * page_size
    end = start + page_size
    return DocumentListResponse(items=docs[start:end], total=len(docs), page=page, page_size=page_size)

@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    doc = fake_store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: str):
    if document_id not in fake_store:
        raise HTTPException(status_code=404, detail="Document not found")
    del fake_store[document_id]
    return {"message": "Document and associated data deleted."}
