"""
Neo4j Generic API Router

Generic CRUD API for Neo4j operations.
This API can be called by Java backend for any Neo4j operations.

All endpoints use x-internal-token for authentication.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Header

from edukg.core.neo4j.service import Neo4jService, get_neo4j_service
from config.settings import settings

router = APIRouter(prefix="/api/neo4j", tags=["Neo4j"])


def verify_internal_token(x_internal_token: str = Header(None)):
    """Verify internal token for Java backend calls."""
    if not x_internal_token or x_internal_token != settings.INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")
    return True


def get_service() -> Neo4jService:
    """Dependency injection for Neo4j service."""
    return get_neo4j_service()


@router.get("/health")
async def health_check(
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Check Neo4j connection health.

    Can be called by Java backend to verify Neo4j connectivity.
    """
    return service.health_check()


@router.get("/stats")
async def get_stats(
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Get database statistics.

    Returns counts of nodes by label and total relationships.
    """
    return service.get_database_stats()


# ============ Node Operations ============

@router.post("/nodes/{label}")
async def create_node(
    label: str = Path(..., description="Node label"),
    properties: Dict[str, Any] = ...,
    merge_on: Optional[str] = Query(None, description="Property to merge on"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Create a node.

    Java backend can call this to create any type of node.

    Example:
        POST /api/neo4j/nodes/Entity?merge_on=uri
        Body: {"uri": "xxx", "label": "test", "subject": "math"}
    """
    result = service.create_node(label, properties, merge_on)
    return {"success": True, "node": result}


@router.post("/nodes/{label}/batch")
async def create_nodes_batch(
    label: str = Path(..., description="Node label"),
    items: List[Dict[str, Any]] = ...,
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Create multiple nodes in batch.

    Example:
        POST /api/neo4j/nodes/Entity/batch
        Body: [{"uri": "a", "label": "A"}, {"uri": "b", "label": "B"}]
    """
    result = service.create_nodes_batch(label, items)
    return {"success": True, **result}


@router.get("/nodes/{label}")
async def find_nodes(
    label: str = Path(..., description="Node label"),
    id_property: str = Query("id", description="ID property name"),
    id_value: Optional[str] = Query(None, description="ID value"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Find nodes by label and optional ID.

    Example:
        GET /api/neo4j/nodes/Entity?id_property=uri&id_value=xxx
    """
    if id_value:
        node = service.find_node(label, id_value, id_property)
        return {"nodes": [node] if node else []}

    nodes = service.find_nodes(label, limit=limit)
    return {"nodes": nodes, "count": len(nodes)}


@router.get("/nodes/{label}/search")
async def search_nodes(
    label: str = Path(..., description="Node label"),
    property_name: str = Query(..., description="Property to search"),
    pattern: str = Query(..., description="Search pattern"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Search nodes by property pattern (CONTAINS).

    Example:
        GET /api/neo4j/nodes/Entity/search?property_name=label&pattern=方程
    """
    nodes = service.search_nodes(label, property_name, pattern, limit)
    return {"nodes": nodes, "count": len(nodes)}


@router.put("/nodes/{label}")
async def update_node(
    label: str = Path(..., description="Node label"),
    match_property: str = Query(..., description="Property to match on"),
    match_value: str = Query(..., description="Property value"),
    updates: Dict[str, Any] = ...,
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Update a node.

    Example:
        PUT /api/neo4j/nodes/Entity?match_property=uri&match_value=xxx
        Body: {"label": "updated label"}
    """
    result = service.update_node(label, match_property, match_value, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"success": True, "node": result}


@router.delete("/nodes/{label}")
async def delete_node(
    label: str = Path(..., description="Node label"),
    match_property: str = Query(..., description="Property to match on"),
    match_value: str = Query(..., description="Property value"),
    detach: bool = Query(False, description="Also delete relationships"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Delete a node.

    Example:
        DELETE /api/neo4j/nodes/Entity?match_property=uri&match_value=xxx&detach=true
    """
    result = service.delete_node(label, match_property, match_value, detach)
    return {"success": True, **result}


@router.get("/nodes/{label}/count")
async def count_nodes(
    label: str = Path(..., description="Node label"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Count nodes by label.

    Example:
        GET /api/neo4j/nodes/Entity/count
    """
    count = service.count_nodes(label)
    return {"label": label, "count": count}


# ============ Relationship Operations ============

@router.post("/relationships")
async def create_relationship(
    from_label: str = Query(..., description="Source node label"),
    from_id: str = Query(..., description="Source node ID"),
    to_label: str = Query(..., description="Target node label"),
    to_id: str = Query(..., description="Target node ID"),
    relation_type: str = Query(..., description="Relationship type"),
    properties: Optional[Dict[str, Any]] = None,
    id_property: str = Query("id", description="ID property name"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Create a relationship between nodes.

    Example:
        POST /api/neo4j/relationships?from_label=Student&from_id=s1&to_label=Entity&to_id=e1&relation_type=LEARNED
        Body: {"status": "mastered", "score": 95}
    """
    result = service.create_relationship(
        from_label, from_id, to_label, to_id, relation_type, properties, id_property
    )
    return {"success": True, **result}


@router.get("/relationships")
async def get_relationships(
    label: str = Query(..., description="Node label"),
    node_id: str = Query(..., description="Node ID"),
    relation_type: Optional[str] = Query(None, description="Filter by relationship type"),
    direction: str = Query("outgoing", description="outgoing, incoming, or both"),
    id_property: str = Query("id", description="ID property name"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Get relationships for a node.

    Example:
        GET /api/neo4j/relationships?label=Student&node_id=s1&direction=outgoing
    """
    relationships = service.get_relationships(
        label, node_id, relation_type, direction, id_property
    )
    return {"relationships": relationships, "count": len(relationships)}


# ============ Raw Query ============

@router.post("/query")
async def execute_query(
    query: str = ...,
    parameters: Optional[Dict[str, Any]] = None,
    read_only: bool = Query(True, description="Use read transaction"),
    service: Neo4jService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    """
    Execute a raw Cypher query.

    **WARNING**: This endpoint allows arbitrary Cypher execution.
    Use with caution in production.

    Example:
        POST /api/neo4j/query
        Body: {"query": "MATCH (n:Entity) WHERE n.subject = $subject RETURN n", "parameters": {"subject": "math"}}
    """
    results = service.execute_query(query, parameters, read_only)
    return {"results": results, "count": len(results)}