"""
Knowledge Graph Service

Business logic layer for knowledge graph operations.
Combines Neo4j queries with entity linking.
"""
import logging
from typing import Optional, List, Dict, Any

from edukg.core.neo4j import get_neo4j_client, Neo4jClient
from edukg.core.kg.entity_linker import get_entity_linker, EntityLinker
from edukg.models.kg import (
    EntityResponse,
    EntitySearchResponse,
    EntityLinkResponse,
    LinkedEntityResponse,
    KnowledgeTreeNode,
    KnowledgeTreeResponse,
    SubjectClassesResponse,
    SubjectClassResponse,
    StudentProgressItem,
    StudentProgressResponse,
    StudentProgressUpdateResponse,
    ProgressStatus,
    ProgressStatistics,
    StudentStatisticsResponse,
    KnowledgeRecommendation,
    RecommendationResponse,
    LearningPathItem,
    LearningPathResponse,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    Service layer for knowledge graph operations.

    Combines:
    - Neo4j queries for graph data
    - Entity linker for text analysis
    """

    def __init__(self):
        self._neo4j: Optional[Neo4jClient] = None
        self._linker: Optional[EntityLinker] = None

    @property
    def neo4j(self) -> Neo4jClient:
        """Get Neo4j client lazily."""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    @property
    def linker(self) -> EntityLinker:
        """Get entity linker lazily."""
        if self._linker is None:
            self._linker = get_entity_linker()
        return self._linker

    # ============ Entity Operations ============

    def search_entities(
        self,
        label: str,
        subject: Optional[str] = None,
        limit: int = 20
    ) -> EntitySearchResponse:
        """
        Search entities by label.

        Args:
            label: Label to search for
            subject: Optional subject filter
            limit: Maximum results

        Returns:
            EntitySearchResponse with matching entities
        """
        # Use entity linker for dictionary search
        entities = self.linker.search(label, subject, limit)

        return EntitySearchResponse(
            total=len(entities),
            entities=entities
        )

    def get_entity(self, uri: str) -> Optional[EntityResponse]:
        """
        Get entity details by URI.

        Args:
            uri: Entity URI

        Returns:
            EntityResponse or None if not found
        """
        # Query Neo4j for entity
        query = """
        MATCH (e:Entity {uri: $uri})
        OPTIONAL MATCH (e)-[r]->(related)
        RETURN e.label AS label,
               e.subject AS subject,
               e.description AS description,
               e AS properties,
               collect(DISTINCT {type: type(r), target: related.label}) AS relations
        """

        result = self.neo4j.execute_query(query, {"uri": uri})

        if not result:
            return None

        record = result[0]

        return EntityResponse(
            uri=uri,
            label=record.get("label", ""),
            subject=record.get("subject"),
            description=record.get("description"),
            properties=[],
            relationships={}
        )

    def link_entities(
        self,
        text: str,
        subject: Optional[str] = None,
        enrich_context: bool = False
    ) -> EntityLinkResponse:
        """
        Identify entities in text.

        Args:
            text: Text to analyze
            subject: Optional subject filter
            enrich_context: Whether to include context from KG

        Returns:
            EntityLinkResponse with linked entities
        """
        # Use entity linker
        linked = self.linker.link(text, subject, enrich_context)

        # Convert to response format
        entities = []
        for entity in linked:
            entities.append(LinkedEntityResponse(
                label=entity.label,
                uri=entity.uri,
                subject=entity.subject,
                positions=[{"start": entity.start, "end": entity.end}],
                context=entity.context
            ))

        return EntityLinkResponse(entities=entities)

    # ============ Knowledge Tree Operations ============

    def get_knowledge_tree(
        self,
        subject: str,
        depth: int = 3,
        student_id: Optional[str] = None
    ) -> KnowledgeTreeResponse:
        """
        Get knowledge tree for a subject.

        Args:
            subject: Subject name
            depth: Tree depth
            student_id: Optional student ID for progress

        Returns:
            KnowledgeTreeResponse
        """
        # Get entities for this subject
        query = """
        MATCH (e:Entity {subject: $subject})
        WHERE e.label <> ''
        RETURN e.uri AS uri, e.label AS label
        LIMIT 100
        """

        result = self.neo4j.execute_query(query, {"subject": subject})

        # Build tree structure (simplified - flat list for now)
        children = []
        for record in result:
            node = KnowledgeTreeNode(
                id=record["uri"],
                label=record["label"],
                type="entity",
                subject=subject
            )
            children.append(node)

        root = KnowledgeTreeNode(
            id="root",
            label=self._subject_name_cn(subject),
            type="class",
            subject=subject,
            children=children
        )

        return KnowledgeTreeResponse(subject=subject, tree=root)

    def get_subject_classes(self, subject: str) -> SubjectClassesResponse:
        """
        Get classes/categories for a subject.

        Args:
            subject: Subject name

        Returns:
            SubjectClassesResponse
        """
        # Query for distinct classes (simplified)
        query = """
        MATCH (e:Entity {subject: $subject})
        RETURN DISTINCT e.subject AS subject, count(e) AS count
        """

        result = self.neo4j.execute_query(query, {"subject": subject})

        classes = []
        for record in result:
            classes.append(SubjectClassResponse(
                uri=f"http://edukg.org/class/{subject}",
                label=self._subject_name_cn(subject),
                entity_count=record.get("count", 0)
            ))

        return SubjectClassesResponse(classes=classes)

    # ============ Student Progress Operations ============

    def get_student_progress(
        self,
        student_id: str,
        subject: Optional[str] = None
    ) -> StudentProgressResponse:
        """
        Get student learning progress.

        Args:
            student_id: Student identifier
            subject: Optional subject filter

        Returns:
            StudentProgressResponse
        """
        query = """
        MATCH (s:Student {id: $student_id})-[l:LEARNED]->(e:Entity)
        RETURN e.uri AS uri, e.label AS label, e.subject AS subject,
               l.status AS status, l.score AS score, l.timestamp AS updated_at
        """

        params = {"student_id": student_id}
        if subject:
            query += " WHERE e.subject = $subject"
            params["subject"] = subject

        result = self.neo4j.execute_query(query, params)

        progress = []
        for record in result:
            progress.append(StudentProgressItem(
                entity_uri=record["uri"],
                entity_label=record["label"],
                subject=record["subject"],
                status=ProgressStatus(record.get("status", "not_started")),
                score=record.get("score"),
                updated_at=record.get("updated_at")
            ))

        return StudentProgressResponse(student_id=student_id, progress=progress)

    def update_student_progress(
        self,
        student_id: str,
        entity_uri: str,
        status: ProgressStatus,
        score: Optional[int] = None
    ) -> StudentProgressUpdateResponse:
        """
        Update student learning progress.

        Args:
            student_id: Student identifier
            entity_uri: Entity URI
            status: Progress status
            score: Optional score

        Returns:
            StudentProgressUpdateResponse
        """
        # Ensure student exists
        create_student = "MERGE (s:Student {id: $student_id})"

        # Create/update progress relationship
        update_query = """
        MATCH (s:Student {id: $student_id})
        MATCH (e:Entity {uri: $entity_uri})
        MERGE (s)-[l:LEARNED]->(e)
        SET l.status = $status, l.score = $score, l.timestamp = datetime()
        RETURN e.label AS label, e.subject AS subject
        """

        try:
            self.neo4j.execute_write(create_student, {"student_id": student_id})
            result = self.neo4j.execute_query(update_query, {
                "student_id": student_id,
                "entity_uri": entity_uri,
                "status": status.value,
                "score": score
            })

            if result:
                record = result[0]
                return StudentProgressUpdateResponse(
                    success=True,
                    progress=StudentProgressItem(
                        entity_uri=entity_uri,
                        entity_label=record["label"],
                        subject=record["subject"],
                        status=status,
                        score=score
                    )
                )
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

        return StudentProgressUpdateResponse(success=False)

    def get_student_statistics(self, student_id: str) -> StudentStatisticsResponse:
        """
        Get student progress statistics.

        Args:
            student_id: Student identifier

        Returns:
            StudentStatisticsResponse
        """
        # Overall statistics
        overall_query = """
        MATCH (s:Student {id: $student_id})-[l:LEARNED]->(e:Entity)
        RETURN l.status AS status, count(e) AS count
        """

        result = self.neo4j.execute_query(overall_query, {"student_id": student_id})

        mastered = in_progress = not_started = 0
        for record in result:
            status = record.get("status", "not_started")
            count = record.get("count", 0)
            if status == "mastered":
                mastered = count
            elif status == "in_progress":
                in_progress = count
            else:
                not_started = count

        return StudentStatisticsResponse(
            student_id=student_id,
            overall=ProgressStatistics(
                total=mastered + in_progress + not_started,
                mastered=mastered,
                in_progress=in_progress,
                not_started=not_started
            ),
            by_subject=[]
        )

    # ============ Recommendation Operations ============

    def get_recommendations(
        self,
        entity_uri: Optional[str] = None,
        subject: Optional[str] = None,
        student_id: Optional[str] = None,
        limit: int = 10
    ) -> RecommendationResponse:
        """
        Get knowledge point recommendations.

        Args:
            entity_uri: Based on this entity
            subject: Subject filter
            student_id: Student for personalized recommendations
            limit: Maximum recommendations

        Returns:
            RecommendationResponse
        """
        # Simple recommendation: related entities
        query = """
        MATCH (e:Entity {uri: $uri})-[r]->(related:Entity)
        RETURN related.uri AS uri, related.label AS label, related.subject AS subject
        LIMIT $limit
        """

        params = {"uri": entity_uri, "limit": limit}

        result = self.neo4j.execute_query(query, params) if entity_uri else []

        recommendations = []
        for record in result:
            recommendations.append(KnowledgeRecommendation(
                entity_uri=record["uri"],
                label=record["label"],
                reason="Related to current knowledge point",
                mastered=False
            ))

        return RecommendationResponse(recommendations=recommendations)

    def get_learning_path(
        self,
        target_entity_uri: str,
        student_id: str
    ) -> LearningPathResponse:
        """
        Get learning path to a target knowledge point.

        Args:
            target_entity_uri: Target entity URI
            student_id: Student identifier

        Returns:
            LearningPathResponse
        """
        # Simplified: just return the target entity
        query = """
        MATCH (e:Entity {uri: $uri})
        RETURN e.uri AS uri, e.label AS label
        """

        result = self.neo4j.execute_query(query, {"uri": target_entity_uri})

        if result:
            record = result[0]
            return LearningPathResponse(path=[
                LearningPathItem(
                    order=1,
                    entity_uri=record["uri"],
                    label=record["label"],
                    status=ProgressStatus.NOT_STARTED
                )
            ])

        return LearningPathResponse(path=[])

    # ============ Helper Methods ============

    def _subject_name_cn(self, subject: str) -> str:
        """Get Chinese name for subject."""
        names = {
            "math": "数学",
            "physics": "物理",
            "chemistry": "化学",
            "biology": "生物",
            "chinese": "语文",
            "history": "历史",
            "geo": "地理",
            "politics": "政治",
            "english": "英语",
        }
        return names.get(subject, subject)


# Global singleton
_kg_service: Optional[KnowledgeGraphService] = None


def get_kg_service() -> KnowledgeGraphService:
    """Get knowledge graph service instance."""
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    return _kg_service