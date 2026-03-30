"""
Neo4j Service

High-level service for Neo4j operations.
This module provides generic operations that can be exposed to Java backend.

All methods are designed to be called via API endpoints.
"""
import logging
from typing import Optional, List, Dict, Any

from edukg.core.neo4j.client import Neo4jClient, get_neo4j_client
from edukg.core.neo4j.repository import Neo4jRepository

logger = logging.getLogger(__name__)


class Neo4jService:
    """
    High-level service for Neo4j operations.

    Provides generic CRUD operations for any label.
    Can be exposed to Java backend via REST API.

    Usage:
        service = Neo4jService()
        service.create_node("Entity", {"uri": "xxx", "label": "test"})
        service.find_nodes("Entity", {"uri": "xxx"})
    """

    def __init__(self, client: Neo4jClient = None):
        """
        Initialize service.

        Args:
            client: Optional Neo4j client
        """
        self._client = client or get_neo4j_client()
        self._repositories: Dict[str, Neo4jRepository] = {}

    def _get_repository(self, label: str) -> Neo4jRepository:
        """Get or create repository for a label."""
        if label not in self._repositories:
            self._repositories[label] = Neo4jRepository(label, self._client)
        return self._repositories[label]

    # ============ Connection Management ============

    def health_check(self) -> Dict[str, Any]:
        """
        Check Neo4j connection health.

        Returns:
            Health status with version info
        """
        is_healthy = self._client.health_check()
        version = self._client.get_version() if is_healthy else None

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "version": version,
            "connected": is_healthy
        }

    # ============ Node Operations ============

    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        merge_on: str = None
    ) -> Dict[str, Any]:
        """
        Create a node.

        Args:
            label: Node label
            properties: Node properties
            merge_on: Property to merge on (optional, creates if not exists)

        Returns:
            Created node properties
        """
        repo = self._get_repository(label)

        if merge_on:
            return repo.merge(merge_on, properties)
        return repo.create(properties)

    def create_nodes_batch(
        self,
        label: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple nodes in batch.

        Args:
            label: Node label
            items: List of node properties

        Returns:
            Result with count
        """
        repo = self._get_repository(label)
        count = repo.create_many(items)
        return {"created": count, "label": label}

    def find_node(
        self,
        label: str,
        id_value: Any,
        id_property: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single node by ID.

        Args:
            label: Node label
            id_value: ID value
            id_property: ID property name

        Returns:
            Node properties or None
        """
        repo = self._get_repository(label)
        return repo.find_by_id(id_value, id_property)

    def find_nodes(
        self,
        label: str,
        properties: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find nodes by properties.

        Args:
            label: Node label
            properties: Optional property filters
            limit: Maximum results

        Returns:
            List of node properties
        """
        repo = self._get_repository(label)

        if not properties:
            return repo.find_all(limit)
        return repo.find_by_properties(properties)

    def search_nodes(
        self,
        label: str,
        property_name: str,
        pattern: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search nodes by property pattern.

        Args:
            label: Node label
            property_name: Property to search
            pattern: Search pattern (CONTAINS)
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        repo = self._get_repository(label)
        return repo.search(property_name, pattern, limit)

    def update_node(
        self,
        label: str,
        match_property: str,
        match_value: Any,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a node.

        Args:
            label: Node label
            match_property: Property to match on
            match_value: Property value
            updates: Properties to update

        Returns:
            Updated node properties or None
        """
        repo = self._get_repository(label)
        return repo.update(match_property, match_value, updates)

    def delete_node(
        self,
        label: str,
        match_property: str,
        match_value: Any,
        detach: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a node.

        Args:
            label: Node label
            match_property: Property to match on
            match_value: Property value
            detach: Also delete relationships

        Returns:
            Result with success status
        """
        repo = self._get_repository(label)
        success = repo.delete(match_property, match_value, detach)
        return {"deleted": success, "label": label, match_property: match_value}

    def count_nodes(self, label: str) -> int:
        """
        Count nodes by label.

        Args:
            label: Node label

        Returns:
            Total count
        """
        repo = self._get_repository(label)
        return repo.count()

    # ============ Relationship Operations ============

    def create_relationship(
        self,
        from_label: str,
        from_id: Any,
        to_label: str,
        to_id: Any,
        relation_type: str,
        properties: Dict[str, Any] = None,
        id_property: str = "id"
    ) -> Dict[str, Any]:
        """
        Create a relationship between nodes.

        Args:
            from_label: Source node label
            from_id: Source node ID
            to_label: Target node label
            to_id: Target node ID
            relation_type: Relationship type
            properties: Optional relationship properties
            id_property: ID property name

        Returns:
            Result status
        """
        repo = self._get_repository(from_label)
        success = repo.create_relationship(
            from_id, to_label, to_id, relation_type, properties, id_property
        )
        return {
            "created": success,
            "from": {"label": from_label, "id": from_id},
            "to": {"label": to_label, "id": to_id},
            "type": relation_type
        }

    def get_relationships(
        self,
        label: str,
        node_id: Any,
        relation_type: str = None,
        direction: str = "outgoing",
        id_property: str = "id"
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a node.

        Args:
            label: Node label
            node_id: Node ID
            relation_type: Optional filter by type
            direction: "outgoing", "incoming", or "both"
            id_property: ID property name

        Returns:
            List of relationships
        """
        repo = self._get_repository(label)
        return repo.get_relationships(node_id, relation_type, direction, id_property)

    # ============ Raw Query ============

    def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        read_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw Cypher query.

        Args:
            query: Cypher query
            parameters: Query parameters
            read_only: If True, use read transaction

        Returns:
            Query results
        """
        if read_only:
            return self._client.execute_read(query, parameters)
        return self._client.execute_write(query, parameters)

    # ============ Statistics ============

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics including node and relationship counts
        """
        # Get all labels
        labels_query = "CALL db.labels() YIELD label RETURN label"
        labels = self._client.execute_read(labels_query)

        stats = {"labels": {}}

        for label_row in labels:
            label = label_row["label"]
            count_query = f"MATCH (n:`{label}`) RETURN count(n) AS count"
            count_result = self._client.execute_read(count_query)
            stats["labels"][label] = count_result[0]["count"] if count_result else 0

        # Total relationship count
        rel_query = "MATCH ()-[r]->() RETURN count(r) AS count"
        rel_result = self._client.execute_read(rel_query)
        stats["total_relationships"] = rel_result[0]["count"] if rel_result else 0

        return stats


# Global singleton
_neo4j_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """Get Neo4j service instance."""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service