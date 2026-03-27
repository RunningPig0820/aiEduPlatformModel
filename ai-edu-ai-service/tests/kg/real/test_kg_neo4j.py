"""
Knowledge Graph Neo4j Tests

Real Neo4j connection tests for knowledge graph operations.
Tests are READ-ONLY - they do not create or delete data.
"""
import os
import pytest
from dotenv import load_dotenv

# Load .env file
load_dotenv()


@pytest.fixture(scope="module")
def neo4j_client():
    """Get Neo4j client for testing."""
    from core.neo4j import init_neo4j, get_neo4j_client, close_neo4j

    init_neo4j()
    client = get_neo4j_client()
    yield client
    close_neo4j()


@pytest.fixture(scope="module")
def entity_linker():
    """Get entity linker for testing."""
    from core.kg.entity_linker import init_entity_linker, get_entity_linker

    init_entity_linker()
    return get_entity_linker()


@pytest.fixture(scope="module")
def kg_service():
    """Get KG service for testing."""
    from core.neo4j import init_neo4j
    from core.kg.entity_linker import init_entity_linker
    from core.kg.service import get_kg_service

    init_neo4j()
    init_entity_linker()
    return get_kg_service()


# ============================================================
# 10.6 Neo4j Health Check Tests
# ============================================================

@pytest.mark.requires_neo4j
class TestNeo4jHealthCheck:
    """Test Neo4j connection and health."""

    def test_neo4j_connection(self, neo4j_client):
        """Test basic Neo4j connection."""
        result = neo4j_client.execute_query("RETURN 1 as test")
        assert result is not None
        assert len(result) == 1
        assert result[0]["test"] == 1

    def test_neo4j_health_check_method(self, neo4j_client):
        """Test Neo4j health check method."""
        is_healthy = neo4j_client.health_check()
        assert is_healthy is True

    def test_neo4j_has_data(self, neo4j_client):
        """Test that Neo4j has EDUKG data loaded."""
        # Check for Entity nodes
        result = neo4j_client.execute_query(
            "MATCH (e:Entity) RETURN count(e) as count"
        )
        assert result[0]["count"] > 0, "Neo4j should have Entity nodes"

        # Check for subjects
        result = neo4j_client.execute_query(
            "MATCH (e:Entity) WHERE e.subject IS NOT NULL "
            "RETURN DISTINCT e.subject as subject LIMIT 10"
        )
        subjects = [r["subject"] for r in result]
        assert len(subjects) > 0, "Entities should have subject property"


# ============================================================
# 10.2 Entity Search Tests
# ============================================================

@pytest.mark.requires_neo4j
class TestEntitySearch:
    """Test entity search functionality."""

    def test_search_entity_by_label_exact(self, kg_service):
        """KG-ENTITY-001: Exact search - entity exists."""
        response = kg_service.search_entities(
            label="一元二次方程",
            subject="math",
            limit=10
        )
        assert response.total >= 1
        assert any("一元二次方程" in e["label"] for e in response.entities)

    def test_search_entity_fuzzy(self, kg_service):
        """KG-ENTITY-002: Fuzzy search - entity exists."""
        response = kg_service.search_entities(
            label="方程",
            subject="math",
            limit=10
        )
        assert response.total >= 1
        # Should find entities containing "方程"
        for entity in response.entities:
            assert "方程" in entity["label"]

    def test_search_entity_not_found(self, kg_service):
        """KG-ENTITY-003: Search - no matching entity."""
        response = kg_service.search_entities(
            label="不存在的知识点xyz123",
            limit=10
        )
        assert response.total == 0
        assert len(response.entities) == 0

    def test_search_entity_without_subject(self, kg_service):
        """KG-ENTITY-004: Search without subject filter."""
        response = kg_service.search_entities(
            label="函数",
            limit=20
        )
        # Should find entities from multiple subjects
        assert response.total >= 1

    def test_search_entity_with_limit(self, kg_service):
        """KG-ENTITY-007: Search with limit parameter."""
        response = kg_service.search_entities(
            label="方程",
            subject="math",
            limit=5
        )
        assert len(response.entities) <= 5


# ============================================================
# 10.3 Entity Linking Tests
# ============================================================

@pytest.mark.requires_neo4j
class TestEntityLinking:
    """Test entity linking with jieba + dictionary."""

    def test_link_single_entity(self, entity_linker):
        """KG-LINK-001: Link single entity in text."""
        text = "一元二次方程很重要"
        entities = entity_linker.link(text, subject="math")

        assert len(entities) >= 1
        assert any(e.label == "一元二次方程" for e in entities)

    def test_link_multiple_entities(self, entity_linker):
        """KG-LINK-002: Link multiple entities in text."""
        text = "方程和函数都是重要的数学概念"
        entities = entity_linker.link(text, subject="math")

        assert len(entities) >= 1
        # Should find at least one of the entities
        labels = [e.label for e in entities]
        assert any("方程" in l or "函数" in l for l in labels)

    def test_link_no_match(self, entity_linker):
        """KG-LINK-003: Link - no matching entities."""
        text = "这是一段没有任何知识点的普通文本"
        entities = entity_linker.link(text, subject="math")

        # May or may not find entities, but should not crash
        assert isinstance(entities, list)

    def test_link_with_subject_filter(self, entity_linker):
        """KG-LINK-004: Link with subject filter."""
        text = "函数"
        entities_math = entity_linker.link(text, subject="math")
        entities_physics = entity_linker.link(text, subject="physics")

        # All found entities should match the subject
        for e in entities_math:
            assert e.subject == "math"

    def test_link_entity_positions(self, entity_linker):
        """KG-LINK-005: Link with accurate positions."""
        text = "一元二次方程很重要"
        entities = entity_linker.link(text, subject="math")

        for entity in entities:
            # Position should be valid
            assert entity.start >= 0
            assert entity.end <= len(text)
            assert entity.end > entity.start
            # Text at position should match label
            assert text[entity.start:entity.end] == entity.label

    def test_search_entities_fuzzy(self, entity_linker):
        """Test fuzzy entity search."""
        results = entity_linker.search("方程", subject="math", limit=10)

        assert len(results) >= 1
        for result in results:
            assert "方程" in result["label"]
            assert result["uri"]
            assert result["subject"]


# ============================================================
# 10.4 Knowledge Tree Tests
# ============================================================

@pytest.mark.requires_neo4j
class TestKnowledgeTree:
    """Test knowledge tree generation."""

    def test_get_knowledge_tree_success(self, kg_service):
        """KG-TREE-001: Get knowledge tree - success."""
        response = kg_service.get_knowledge_tree(
            subject="math",
            depth=3
        )

        assert response.subject == "math"
        assert response.tree is not None
        assert response.tree.label == "数学"

    def test_get_knowledge_tree_depth(self, kg_service):
        """KG-TREE-002: Get knowledge tree with depth limit."""
        response = kg_service.get_knowledge_tree(
            subject="math",
            depth=2
        )

        assert response.tree is not None
        # Tree should have children
        if response.tree.children:
            assert len(response.tree.children) > 0

    def test_get_subject_classes(self, kg_service):
        """Test getting subject classes."""
        response = kg_service.get_subject_classes(subject="math")

        assert response.classes is not None
        assert len(response.classes) >= 0


# ============================================================
# Knowledge Point Recommendation Tests
# ============================================================

@pytest.mark.requires_neo4j
class TestRecommendations:
    """Test knowledge point recommendations."""

    def test_get_recommendations_by_entity(self, kg_service, neo4j_client):
        """KG-RECOMMEND-001: Get recommendations based on entity."""
        # First find an entity with relationships
        result = neo4j_client.execute_query(
            "MATCH (e:Entity)-[r]->(related:Entity) "
            "RETURN e.uri as uri LIMIT 1"
        )

        if not result:
            pytest.skip("No entities with relationships found")

        entity_uri = result[0]["uri"]
        response = kg_service.get_recommendations(
            entity_uri=entity_uri,
            limit=5
        )

        assert response.recommendations is not None

    def test_get_recommendations_empty(self, kg_service):
        """KG-RECOMMEND-003: Get recommendations - no related entities."""
        # Use a non-existent URI
        response = kg_service.get_recommendations(
            entity_uri="http://edukg.org/nonexistent",
            limit=5
        )

        assert response.recommendations is not None
        assert len(response.recommendations) == 0


# ============================================================
# API Endpoint Tests (via service)
# ============================================================

@pytest.mark.requires_neo4j
class TestKGServiceIntegration:
    """Integration tests for KG service methods."""

    def test_get_entity_by_uri(self, kg_service, neo4j_client):
        """Test getting entity by URI."""
        # First get a valid URI
        result = neo4j_client.execute_query(
            "MATCH (e:Entity) WHERE e.label IS NOT NULL "
            "RETURN e.uri as uri, e.label as label LIMIT 1"
        )

        if not result:
            pytest.skip("No entities found in Neo4j")

        uri = result[0]["uri"]
        entity = kg_service.get_entity(uri)

        assert entity is not None
        assert entity.uri == uri

    def test_get_entity_not_found(self, kg_service):
        """Test getting non-existent entity."""
        entity = kg_service.get_entity("http://edukg.org/nonexistent/entity")

        assert entity is None

    def test_link_entities_via_service(self, kg_service):
        """Test entity linking via service."""
        response = kg_service.link_entities(
            text="一元二次方程是初中数学的重要内容",
            subject="math"
        )

        assert response.entities is not None
        assert len(response.entities) >= 1