"""
Neo4j Repository

Generic repository pattern for Neo4j operations.
Provides high-level CRUD operations that can be used by any domain.
"""
import logging
from typing import Optional, List, Dict, Any, TypeVar, Generic

from edukg.core.neo4j.client import Neo4jClient, get_neo4j_client

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Neo4jRepository:
    """
    Generic repository for Neo4j CRUD operations.

    Usage:
        repo = Neo4jRepository("Entity")
        repo.create({"uri": "xxx", "label": "test"})
        repo.find_by_property("uri", "xxx")
        repo.update("uri", "xxx", {"label": "updated"})
        repo.delete("uri", "xxx")
    """

    def __init__(self, label: str, client: Neo4jClient = None):
        """
        Initialize repository for a specific node label.

        Args:
            label: Node label (e.g., "Entity", "Student", "User")
            client: Optional Neo4j client (uses singleton if not provided)
        """
        self._label = label
        self._client = client or get_neo4j_client()

    # ============ Create Operations ============

    def create(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new node.

        Args:
            properties: Node properties

        Returns:
            Created node properties
        """
        query = f"""
        CREATE (n:{self._label} $properties)
        RETURN properties(n) AS props
        """
        result = self._client.execute_write(query, {"properties": properties})
        return result[0]["props"] if result else {}

    def create_many(self, items: List[Dict[str, Any]]) -> int:
        """
        Create multiple nodes in batch.

        Args:
            items: List of property dictionaries

        Returns:
            Number of created nodes
        """
        query = f"""
        UNWIND $items AS item
        CREATE (n:{self._label})
        SET n = item
        RETURN count(n) AS created
        """
        result = self._client.execute_write(query, {"items": items})
        return result[0]["created"] if result else 0

    def merge(self, match_property: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a node (MERGE operation).

        Args:
            match_property: Property to match on (e.g., "uri", "id")
            properties: All node properties including match property

        Returns:
            Node properties
        """
        query = f"""
        MERGE (n:{self._label} {{{match_property}: $match_value}})
        SET n += $properties
        RETURN properties(n) AS props
        """
        result = self._client.execute_write(query, {
            "match_value": properties.get(match_property),
            "properties": properties
        })
        return result[0]["props"] if result else {}

    # ============ Read Operations ============

    def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find all nodes.

        Args:
            limit: Maximum results

        Returns:
            List of node properties
        """
        query = f"""
        MATCH (n:{self._label})
        RETURN properties(n) AS props
        LIMIT $limit
        """
        results = self._client.execute_read(query, {"limit": limit})
        return [r["props"] for r in results]

    def find_by_id(self, id_value: Any, id_property: str = "id") -> Optional[Dict[str, Any]]:
        """
        Find a node by ID.

        Args:
            id_value: ID value
            id_property: ID property name (default: "id")

        Returns:
            Node properties or None
        """
        query = f"""
        MATCH (n:{self._label} {{{id_property}: $id_value}})
        RETURN properties(n) AS props
        """
        results = self._client.execute_read(query, {"id_value": id_value})
        return results[0]["props"] if results else None

    def find_by_property(self, property_name: str, value: Any) -> List[Dict[str, Any]]:
        """
        Find nodes by a specific property.

        Args:
            property_name: Property name
            value: Property value

        Returns:
            List of matching nodes
        """
        query = f"""
        MATCH (n:{self._label})
        WHERE n.{property_name} = $value
        RETURN properties(n) AS props
        """
        results = self._client.execute_read(query, {"value": value})
        return [r["props"] for r in results]

    def find_by_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find nodes by multiple properties.

        Args:
            properties: Property filters

        Returns:
            List of matching nodes
        """
        conditions = [f"n.{k} = ${k}" for k in properties.keys()]
        query = f"""
        MATCH (n:{self._label})
        WHERE {' AND '.join(conditions)}
        RETURN properties(n) AS props
        """
        results = self._client.execute_read(query, properties)
        return [r["props"] for r in results]

    def search(self, property_name: str, pattern: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search nodes by property pattern (CONTAINS).

        Args:
            property_name: Property to search
            pattern: Search pattern
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        query = f"""
        MATCH (n:{self._label})
        WHERE n.{property_name} CONTAINS $pattern
        RETURN properties(n) AS props
        LIMIT $limit
        """
        results = self._client.execute_read(query, {"pattern": pattern, "limit": limit})
        return [r["props"] for r in results]

    def count(self) -> int:
        """
        Count all nodes.

        Returns:
            Total count
        """
        query = f"MATCH (n:{self._label}) RETURN count(n) AS count"
        results = self._client.execute_read(query)
        return results[0]["count"] if results else 0

    # ============ Update Operations ============

    def update(self, match_property: str, match_value: Any, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a node by match property.

        Args:
            match_property: Property to match on
            match_value: Property value
            updates: Properties to update

        Returns:
            Updated node properties or None
        """
        query = f"""
        MATCH (n:{self._label} {{{match_property}: $match_value}})
        SET n += $updates
        RETURN properties(n) AS props
        """
        results = self._client.execute_write(query, {
            "match_value": match_value,
            "updates": updates
        })
        return results[0]["props"] if results else None

    def update_many(self, match_property: str, items: List[Dict[str, Any]]) -> int:
        """
        Update multiple nodes.

        Args:
            match_property: Property to match on
            items: List of {match_value, updates} dictionaries

        Returns:
            Number of updated nodes
        """
        query = f"""
        UNWIND $items AS item
        MATCH (n:{self._label} {{{match_property}: item.match_value}})
        SET n += item.updates
        RETURN count(n) AS updated
        """
        params = {
            "items": [
                {"match_value": item["match_value"], "updates": item["updates"]}
                for item in items
            ]
        }
        results = self._client.execute_write(query, params)
        return results[0]["updated"] if results else 0

    # ============ Delete Operations ============

    def delete(self, match_property: str, match_value: Any, detach: bool = False) -> bool:
        """
        Delete a node.

        Args:
            match_property: Property to match on
            match_value: Property value
            detach: Also delete relationships

        Returns:
            True if deleted
        """
        detach_clause = "DETACH " if detach else ""
        query = f"""
        MATCH (n:{self._label} {{{match_property}: $match_value}})
        {detach_clause}DELETE n
        RETURN count(n) AS deleted
        """
        results = self._client.execute_write(query, {"match_value": match_value})
        return results[0]["deleted"] > 0 if results else False

    def delete_many(self, match_property: str, values: List[Any], detach: bool = False) -> int:
        """
        Delete multiple nodes.

        Args:
            match_property: Property to match on
            values: List of property values
            detach: Also delete relationships

        Returns:
            Number of deleted nodes
        """
        detach_clause = "DETACH " if detach else ""
        query = f"""
        MATCH (n:{self._label})
        WHERE n.{match_property} IN $values
        {detach_clause}DELETE n
        RETURN count(n) AS deleted
        """
        results = self._client.execute_write(query, {"values": values})
        return results[0]["deleted"] if results else 0

    # ============ Relationship Operations ============

    def create_relationship(
        self,
        from_id: Any,
        to_label: str,
        to_id: Any,
        relation_type: str,
        relation_properties: Dict[str, Any] = None,
        id_property: str = "id"
    ) -> bool:
        """
        Create a relationship from this node to another.

        Args:
            from_id: Source node ID
            to_label: Target node label
            to_id: Target node ID
            relation_type: Relationship type
            relation_properties: Optional relationship properties
            id_property: ID property name

        Returns:
            True if successful
        """
        props_clause = ""
        params = {"from_id": from_id, "to_id": to_id}

        if relation_properties:
            params["rel_props"] = relation_properties
            props_clause = " SET r += $rel_props"

        query = f"""
        MATCH (a:{self._label} {{{id_property}: $from_id}}), (b:{to_label} {{{id_property}: $to_id}})
        MERGE (a)-[r:{relation_type}]->(b)
        {props_clause}
        RETURN r
        """
        self._client.execute_write(query, params)
        return True

    def get_relationships(
        self,
        node_id: Any,
        relation_type: str = None,
        direction: str = "outgoing",
        id_property: str = "id"
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a node.

        Args:
            node_id: Node ID
            relation_type: Optional filter by relationship type
            direction: "outgoing", "incoming", or "both"
            id_property: ID property name

        Returns:
            List of relationships with connected nodes
        """
        if relation_type:
            rel_pattern = f"[r:{relation_type}]"
        else:
            rel_pattern = "[r]"

        if direction == "outgoing":
            pattern = f"(n){rel_pattern}->(m)"
        elif direction == "incoming":
            pattern = f"(m){rel_pattern}->(n)"
        else:
            pattern = f"(m){rel_pattern}-(n)"

        query = f"""
        MATCH (n:{self._label} {{{id_property}: $node_id}}){pattern}
        RETURN type(r) AS relation_type, properties(r) AS relation_props,
               labels(m) AS target_labels, properties(m) AS target_props
        """
        results = self._client.execute_read(query, {"node_id": node_id})
        return results

    # ============ Raw Query ============

    def execute_custom_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            Query results
        """
        return self._client.execute_read(query, parameters or {})