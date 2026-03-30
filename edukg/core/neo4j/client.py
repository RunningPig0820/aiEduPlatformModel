"""
Neo4j Database Client

Manages connections to Neo4j database with connection pooling,
health checks, and retry logic.

This is a generic client that can be used by any module.
"""
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j database client with connection pooling.

    Usage:
        client = Neo4jClient()
        with client.session() as session:
            result = session.run("MATCH (n) RETURN n LIMIT 10")

    Can be used for generic Neo4j operations, not just knowledge graph.
    """

    _instance: Optional['Neo4jClient'] = None
    _driver: Optional[Driver] = None

    def __new__(cls):
        """Singleton pattern for connection management."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Neo4j driver with connection pooling."""
        if self._driver is not None:
            return

        self._uri = settings.NEO4J_URI
        self._user = settings.NEO4J_USER
        self._password = settings.NEO4J_PASSWORD
        self._max_connection_pool_size = 50
        self._connection_timeout = 30.0

        self._connect()

    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
                max_connection_pool_size=self._max_connection_pool_size,
                connection_timeout=self._connection_timeout,
            )
            logger.info(f"Connected to Neo4j: {self._uri}")
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    @contextmanager
    def session(self, database: str = "neo4j") -> Session:
        """
        Get a Neo4j session.

        Args:
            database: Database name (default: "neo4j")

        Yields:
            Neo4j Session object
        """
        session = self._driver.session(database=database)
        try:
            yield session
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Check if Neo4j connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            return True
        except ServiceUnavailable:
            logger.warning("Neo4j service unavailable")
            return False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

    def get_version(self) -> Optional[str]:
        """
        Get Neo4j server version.

        Returns:
            Version string or None if unavailable
        """
        try:
            with self.session() as session:
                result = session.run("CALL dbms.components() YIELD versions RETURN versions[0] AS version")
                record = result.single()
                return record["version"] if record else None
        except Exception as e:
            logger.error(f"Failed to get Neo4j version: {e}")
            return None

    def close(self):
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    # ============ Generic Query Methods ============

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}
        with self.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]

    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """
        Execute a write transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query result summary
        """
        parameters = parameters or {}

        def _tx_function(tx):
            return tx.run(query, parameters)

        with self.session() as session:
            return session.execute_write(_tx_function)

    def execute_read(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a read transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records
        """
        parameters = parameters or {}

        def _tx_function(tx):
            result = tx.run(query, parameters)
            return [dict(record) for record in result]

        with self.session() as session:
            return session.execute_read(_tx_function)

    # ============ Node Operations ============

    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        merge: bool = False
    ) -> Dict[str, Any]:
        """
        Create a node with given label and properties.

        Args:
            label: Node label
            properties: Node properties
            merge: Use MERGE instead of CREATE

        Returns:
            Created node properties
        """
        op = "MERGE" if merge else "CREATE"
        query = f"""
        {op} (n:{label} $properties)
        RETURN n
        """
        result = self.execute_write(query, {"properties": properties})
        return result

    def find_nodes(
        self,
        label: str = None,
        properties: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find nodes by label and/or properties.

        Args:
            label: Optional node label
            properties: Optional property filters
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        label_clause = f":{label}" if label else ""
        where_clause = ""
        params = {"limit": limit}

        if properties:
            conditions = [f"n.{k} = ${k}" for k in properties.keys()]
            where_clause = "WHERE " + " AND ".join(conditions)
            params.update(properties)

        query = f"""
        MATCH (n{label_clause})
        {where_clause}
        RETURN n
        LIMIT $limit
        """
        return self.execute_read(query, params)

    def update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Update nodes matching criteria.

        Args:
            label: Node label
            match_properties: Properties to match
            update_properties: Properties to update

        Returns:
            Updated nodes
        """
        conditions = [f"n.{k} = ${k}" for k in match_properties.keys()]
        set_clause = ", ".join([f"n.{k} = ${k}_update" for k in update_properties.keys()])

        params = {}
        params.update(match_properties)
        for k, v in update_properties.items():
            params[f"{k}_update"] = v

        query = f"""
        MATCH (n:{label})
        WHERE {' AND '.join(conditions)}
        SET {set_clause}
        RETURN n
        """
        return self.execute_write(query, params)

    def delete_nodes(
        self,
        label: str = None,
        properties: Dict[str, Any] = None,
        detach: bool = False
    ) -> int:
        """
        Delete nodes matching criteria.

        Args:
            label: Optional node label
            properties: Optional property filters
            detach: Also delete relationships

        Returns:
            Number of deleted nodes
        """
        label_clause = f":{label}" if label else ""
        where_clause = ""
        params = {}

        if properties:
            conditions = [f"n.{k} = ${k}" for k in properties.keys()]
            where_clause = "WHERE " + " AND ".join(conditions)
            params.update(properties)

        detach_clause = "DETACH " if detach else ""

        query = f"""
        MATCH (n{label_clause})
        {where_clause}
        {detach_clause}DELETE n
        RETURN count(n) AS deleted
        """
        result = self.execute_write(query, params)
        return result[0]["deleted"] if result else 0

    # ============ Relationship Operations ============

    def create_relationship(
        self,
        from_label: str,
        from_properties: Dict[str, Any],
        to_label: str,
        to_properties: Dict[str, Any],
        relation_type: str,
        relation_properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create a relationship between two nodes.

        Args:
            from_label: Source node label
            from_properties: Source node match properties
            to_label: Target node label
            to_properties: Target node match properties
            relation_type: Relationship type
            relation_properties: Optional relationship properties

        Returns:
            True if successful
        """
        from_conditions = " AND ".join([f"a.{k} = $from_{k}" for k in from_properties.keys()])
        to_conditions = " AND ".join([f"b.{k} = $to_{k}" for k in to_properties.keys()])

        params = {}
        for k, v in from_properties.items():
            params[f"from_{k}"] = v
        for k, v in to_properties.items():
            params[f"to_{k}"] = v

        props_clause = ""
        if relation_properties:
            params["rel_props"] = relation_properties
            props_clause = " $rel_props"

        query = f"""
        MATCH (a:{from_label}), (b:{to_label})
        WHERE {from_conditions} AND {to_conditions}
        MERGE (a)-[r:{relation_type}]->(b)
        {f'SET r += $rel_props' if relation_properties else ''}
        RETURN r
        """
        self.execute_write(query, params)
        return True


# Global singleton instance
neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    Get the Neo4j client singleton instance.

    Returns:
        Neo4jClient instance
    """
    global neo4j_client
    if neo4j_client is None:
        neo4j_client = Neo4jClient()
    return neo4j_client


def init_neo4j():
    """Initialize Neo4j client on application startup."""
    global neo4j_client
    neo4j_client = Neo4jClient()
    logger.info("Neo4j client initialized")


def close_neo4j():
    """Close Neo4j client on application shutdown."""
    global neo4j_client
    if neo4j_client:
        neo4j_client.close()
        neo4j_client = None
        logger.info("Neo4j client closed")