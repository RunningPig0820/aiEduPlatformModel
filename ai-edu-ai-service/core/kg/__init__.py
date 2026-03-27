"""
Knowledge Graph module for EDUKG integration.

This module provides:
- Entity linker for text entity recognition
- Knowledge graph service for business operations

For generic Neo4j operations, use core.neo4j module.
"""
from core.kg.entity_linker import EntityLinker, get_entity_linker, init_entity_linker
from core.kg.service import KnowledgeGraphService, get_kg_service

__all__ = [
    "EntityLinker",
    "get_entity_linker",
    "init_entity_linker",
    "KnowledgeGraphService",
    "get_kg_service",
]