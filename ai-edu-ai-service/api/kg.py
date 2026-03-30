"""
Knowledge Graph API Router

RESTful API endpoints for knowledge graph operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from edukg.models.kg import (
    EntitySearchResponse,
    EntityResponse,
    EntityLinkRequest,
    EntityLinkResponse,
    KnowledgeTreeResponse,
    SubjectClassesResponse,
    StudentProgressResponse,
    StudentProgressUpdateRequest,
    StudentProgressUpdateResponse,
    StudentStatisticsResponse,
    RecommendationResponse,
    LearningPathResponse,
    SubjectEnum,
)
from edukg.core.kg.service import get_kg_service, KnowledgeGraphService

router = APIRouter(prefix="/api/kg", tags=["Knowledge Graph"])


def get_service() -> KnowledgeGraphService:
    """Dependency injection for KG service."""
    return get_kg_service()


@router.get("/entities", response_model=EntitySearchResponse)
async def search_entities(
    label: str = Query(..., min_length=1, max_length=100, description="Entity label to search"),
    subject: Optional[SubjectEnum] = Query(None, description="Filter by subject"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Search knowledge point entities.

    Returns a list of entities matching the search query.
    """
    return service.search_entities(
        label=label,
        subject=subject.value if subject else None,
        limit=limit
    )


@router.get("/entity/{uri:path}", response_model=EntityResponse)
async def get_entity(
    uri: str = Path(..., description="Entity URI"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get entity details by URI.

    Returns detailed information about a knowledge point entity.
    """
    entity = service.get_entity(uri)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/link", response_model=EntityLinkResponse)
async def link_entities(
    request: EntityLinkRequest,
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Identify knowledge point entities in text.

    Analyzes the input text and returns all recognized knowledge point entities.
    """
    return service.link_entities(
        text=request.text,
        subject=request.subject.value if request.subject else None,
        enrich_context=request.enrich_context
    )


@router.get("/subject/{subject}/tree", response_model=KnowledgeTreeResponse)
async def get_knowledge_tree(
    subject: SubjectEnum = Path(..., description="Subject identifier"),
    depth: int = Query(3, ge=1, le=5, description="Tree depth"),
    student_id: Optional[str] = Query(None, description="Student ID for progress"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get knowledge tree for a subject.

    Returns a hierarchical tree structure of knowledge points.
    """
    return service.get_knowledge_tree(
        subject=subject.value,
        depth=depth,
        student_id=student_id
    )


@router.get("/subject/{subject}/classes", response_model=SubjectClassesResponse)
async def get_subject_classes(
    subject: SubjectEnum = Path(..., description="Subject identifier"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get classes/categories for a subject.

    Returns a list of knowledge point categories within the subject.
    """
    return service.get_subject_classes(subject=subject.value)


@router.get("/student/{student_id}/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str = Path(..., description="Student ID"),
    subject: Optional[SubjectEnum] = Query(None, description="Filter by subject"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get student learning progress.

    Returns the learning progress for all knowledge points the student has interacted with.
    """
    return service.get_student_progress(
        student_id=student_id,
        subject=subject.value if subject else None
    )


@router.post("/student/{student_id}/progress", response_model=StudentProgressUpdateResponse)
async def update_student_progress(
    student_id: str = Path(..., description="Student ID"),
    request: StudentProgressUpdateRequest = ...,
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Update student learning progress.

    Creates or updates the student's progress for a specific knowledge point.
    """
    return service.update_student_progress(
        student_id=student_id,
        entity_uri=request.entity_uri,
        status=request.status,
        score=request.score
    )


@router.get("/student/{student_id}/statistics", response_model=StudentStatisticsResponse)
async def get_student_statistics(
    student_id: str = Path(..., description="Student ID"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get student progress statistics.

    Returns overall and per-subject statistics about the student's learning progress.
    """
    return service.get_student_statistics(student_id=student_id)


@router.get("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    entity_uri: Optional[str] = Query(None, description="Based on this entity"),
    subject: Optional[SubjectEnum] = Query(None, description="Subject filter"),
    student_id: Optional[str] = Query(None, description="Student ID for personalization"),
    limit: int = Query(10, ge=1, le=50, description="Maximum recommendations"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get knowledge point recommendations.

    Returns recommended knowledge points based on the provided context.
    """
    return service.get_recommendations(
        entity_uri=entity_uri,
        subject=subject.value if subject else None,
        student_id=student_id,
        limit=limit
    )


@router.get("/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    target_entity_uri: str = Query(..., description="Target knowledge point URI"),
    student_id: str = Query(..., description="Student ID"),
    service: KnowledgeGraphService = Depends(get_service)
):
    """
    Get learning path to a knowledge point.

    Returns an ordered list of knowledge points to learn before reaching the target.
    """
    return service.get_learning_path(
        target_entity_uri=target_entity_uri,
        student_id=student_id
    )