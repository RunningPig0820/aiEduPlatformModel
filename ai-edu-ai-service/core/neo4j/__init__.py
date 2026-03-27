"""
Neo4j Database Module

Provides Neo4j connection management and generic CRUD operations.
This module can be exposed to Java backend via API.

Modules:
    - client: Neo4j connection management with pooling
    - repository: Generic CRUD operations for nodes and relationships
    - service: High-level service for common operations
"""

from core.neo4j.client import Neo4jClient, get_neo4j_client, init_neo4j, close_neo4j
from core.neo4j.repository import Neo4jRepository
from core.neo4j.service import Neo4jService, get_neo4j_service

__all__ = [
    "Neo4jClient",
    "get_neo4j_client",
    "init_neo4j",
    "close_neo4j",
    "Neo4jRepository",
    "Neo4jService",
    "get_neo4j_service",
]