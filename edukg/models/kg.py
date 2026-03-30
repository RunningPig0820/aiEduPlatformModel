"""
Knowledge Graph Data Models

Pydantic models for Knowledge Graph API request/response.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SubjectEnum(str, Enum):
    """Supported subjects."""
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    CHINESE = "chinese"
    HISTORY = "history"
    GEO = "geo"
    POLITICS = "politics"
    ENGLISH = "english"


class ProgressStatus(str, Enum):
    """Student learning progress status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


# ============ Request Models ============

class EntitySearchRequest(BaseModel):
    """Request for searching entities."""
    label: str = Field(..., min_length=1, max_length=100, description="Entity label to search")
    subject: Optional[SubjectEnum] = Field(None, description="Filter by subject")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class EntityLinkRequest(BaseModel):
    """Request for entity linking from text."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    subject: Optional[SubjectEnum] = Field(None, description="Subject context for disambiguation")
    enrich_context: bool = Field(False, description="Include entity context from KG")


class StudentProgressUpdateRequest(BaseModel):
    """Request for updating student progress."""
    entity_uri: str = Field(..., description="Entity URI")
    status: ProgressStatus = Field(..., description="Progress status")
    score: Optional[int] = Field(None, ge=0, le=100, description="Score (0-100)")


# ============ Response Models ============

class EntityResponse(BaseModel):
    """Single entity response."""
    uri: str
    label: str
    subject: Optional[str] = None
    description: Optional[str] = None
    properties: List[Dict[str, str]] = Field(default_factory=list)
    relationships: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)


class EntitySearchResponse(BaseModel):
    """Response for entity search."""
    total: int
    entities: List[Dict[str, str]]


class LinkedEntityResponse(BaseModel):
    """A linked entity found in text."""
    label: str
    uri: str
    subject: Optional[str] = None
    positions: List[Dict[str, int]] = Field(default_factory=list)
    context: Optional[str] = None


class EntityLinkResponse(BaseModel):
    """Response for entity linking."""
    entities: List[LinkedEntityResponse]


class KnowledgeTreeNode(BaseModel):
    """A node in the knowledge tree."""
    id: str
    label: str
    type: str = Field(..., description="Node type: class or entity")
    subject: Optional[str] = None
    progress: Optional[ProgressStatus] = None
    children: List["KnowledgeTreeNode"] = Field(default_factory=list)


class KnowledgeTreeResponse(BaseModel):
    """Response for knowledge tree."""
    subject: str
    tree: KnowledgeTreeNode


class SubjectClassResponse(BaseModel):
    """A class/category in a subject."""
    uri: str
    label: str
    entity_count: int = 0


class SubjectClassesResponse(BaseModel):
    """Response for subject classes."""
    classes: List[SubjectClassResponse]


class StudentProgressItem(BaseModel):
    """A single progress item."""
    entity_uri: str
    entity_label: str
    subject: str
    status: ProgressStatus
    score: Optional[int] = None
    updated_at: Optional[str] = None


class StudentProgressResponse(BaseModel):
    """Response for student progress."""
    student_id: str
    progress: List[StudentProgressItem]


class StudentProgressUpdateResponse(BaseModel):
    """Response for progress update."""
    success: bool
    progress: Optional[StudentProgressItem] = None


class ProgressStatistics(BaseModel):
    """Progress statistics for a student."""
    total: int
    mastered: int
    in_progress: int
    not_started: int


class StudentStatisticsResponse(BaseModel):
    """Response for student statistics."""
    student_id: str
    overall: ProgressStatistics
    by_subject: List[Dict[str, Any]]


class KnowledgeRecommendation(BaseModel):
    """A knowledge point recommendation."""
    entity_uri: str
    label: str
    reason: str
    difficulty: Optional[str] = None
    mastered: bool = False


class RecommendationResponse(BaseModel):
    """Response for recommendations."""
    recommendations: List[KnowledgeRecommendation]


class LearningPathItem(BaseModel):
    """An item in the learning path."""
    order: int
    entity_uri: str
    label: str
    status: ProgressStatus


class LearningPathResponse(BaseModel):
    """Response for learning path."""
    path: List[LearningPathItem]


# Resolve forward reference
KnowledgeTreeNode.model_rebuild()