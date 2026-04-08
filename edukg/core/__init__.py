"""
EDUKG Core Module

Contains knowledge graph, Neo4j modules, and LLM Task Lock infrastructure.
"""

from edukg.core import kg, neo4j
from edukg.core import llmTaskLock

__all__ = ["kg", "neo4j", "llmTaskLock"]