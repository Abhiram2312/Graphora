# apps/backend/api/routers/graph.py
"""Graph router (stub implementations).
Provides basic endpoints for entity lookup, neighbor exploration,
graph overview, and raw Cypher query execution.
These are placeholders – real Neo4j integration will be added in later phases.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid

router = APIRouter()

# ---- Placeholder in‑memory store ---------------------------------------
_fake_entities: Dict[str, Dict[str, Any]] = {}
_fake_edges: List[Dict[str, Any]] = []

# Populate with a tiny demo graph if empty (run once on import)
if not _fake_entities:
    # Example entities
    for name, typ in [("Qwen3", "Concept"), ("Alibaba", "Organization"), ("LLM", "Concept")]:
        eid = str(uuid.uuid4())
        _fake_entities[eid] = {
            "id": eid,
            "name": name,
            "type": typ,
            "description": f"{name} is a {typ.lower()} in the Graphora demo.",
            "confidence": 0.99,
            "source_document_ids": [],
            "source_chunk_ids": [],
        }
    # Example edges (bidirectional for demo)
    ids = list(_fake_entities.keys())
    _fake_edges.append({
        "id": str(uuid.uuid4()),
        "source": ids[0],
        "target": ids[1],
        "relation_type": "developed_by",
        "description": "Qwen3 was developed by Alibaba.",
    })
    _fake_edges.append({
        "id": str(uuid.uuid4()),
        "source": ids[0],
        "target": ids[2],
        "relation_type": "type_of",
        "description": "Qwen3 is a type of LLM.",
    })

# ---- Pydantic models ---------------------------------------------------
class Entity(BaseModel):
    id: str
    name: str
    type: str
    description: str | None = None
    confidence: float | None = None
    source_document_ids: List[str] = []
    source_chunk_ids: List[str] = []

class Edge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    description: str | None = None

class EntityListResponse(BaseModel):
    items: List[Entity]
    total: int

class NeighborResponse(BaseModel):
    nodes: List[Entity]
    edges: List[Edge]

class OverviewResponse(BaseModel):
    entity_count: int
    relationship_count: int
    entity_types: Dict[str, int]
    top_connected_entities: List[Entity]

class CypherRequest(BaseModel):
    cypher: str = Field(..., description="Read‑only Cypher query")

class CypherResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

# ---- Endpoints ----------------------------------------------------------
@router.get("/graph/entities", response_model=EntityListResponse)
async def list_entities(q: str | None = None, type: str | None = None, document_id: str | None = None, page: int = 1, page_size: int = 20):
    # Simple filtering over the placeholder store
    entities = list(_fake_entities.values())
    if q:
        entities = [e for e in entities if q.lower() in e["name"].lower()]
    if type:
        entities = [e for e in entities if e["type"] == type]
    # document_id filter omitted for demo (no linkage)
    start = (page - 1) * page_size
    end = start + page_size
    return EntityListResponse(items=[Entity(**e) for e in entities[start:end]], total=len(entities))

@router.get("/graph/entities/{entity_id}/neighbors", response_model=NeighborResponse)
async def get_neighbors(entity_id: str, depth: int = 1):
    if entity_id not in _fake_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    # For demo we only support depth=1 and return directly connected nodes/edges
    neighbor_edges = [e for e in _fake_edges if e["source"] == entity_id or e["target"] == entity_id]
    neighbor_ids = set()
    for e in neighbor_edges:
        neighbor_ids.add(e["source"])  # include source
        neighbor_ids.add(e["target"])  # include target
    neighbor_ids.discard(entity_id)
    nodes = [Entity(**_fake_entities[nid]) for nid in neighbor_ids]
    edges = [Edge(**e) for e in neighbor_edges]
    return NeighborResponse(nodes=nodes, edges=edges)

@router.get("/graph/overview", response_model=OverviewResponse)
async def graph_overview():
    entity_count = len(_fake_entities)
    relationship_count = len(_fake_edges)
    # Count by type
    type_counts: Dict[str, int] = {}
    for e in _fake_entities.values():
        typ = e["type"]
        type_counts[typ] = type_counts.get(typ, 0) + 1
    # Top connected entities (by degree)
    degree_map: Dict[str, int] = {eid: 0 for eid in _fake_entities}
    for edge in _fake_edges:
        degree_map[edge["source"]] += 1
        degree_map[edge["target"]] += 1
    top_ids = sorted(degree_map, key=degree_map.get, reverse=True)[:5]
    top_entities = [Entity(**_fake_entities[eid]) for eid in top_ids]
    return OverviewResponse(
        entity_count=entity_count,
        relationship_count=relationship_count,
        entity_types=type_counts,
        top_connected_entities=top_entities,
    )

@router.post("/graph/query", response_model=CypherResponse)
async def run_cypher(request: CypherRequest):
    # Very naive parser for demo – only allow limited read‑only queries
    if "DELETE" in request.cypher.upper() or "CREATE" in request.cypher.upper() or "MERGE" in request.cypher.upper():
        raise HTTPException(status_code=403, detail="Write queries are prohibited")
    # Return a static placeholder result
    return CypherResponse(columns=["result"], rows=[["demo"]])
