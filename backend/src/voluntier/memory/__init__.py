"""
Hybrid memory system combining Neo4j graph database and FAISS vector search.

This module provides a unified interface for managing community relationships,
volunteer interactions, and contextual information across the platform.
"""

from .graph_memory import GraphMemory, MemoryNode, MemoryRelationship
from .vector_memory import VectorMemory, EmbeddingModel
from .hybrid_memory import HybridMemorySystem
from .memory_types import (
    MemoryType,
    EntityType,
    RelationshipType,
    MemoryQuery,
    MemoryResult,
    MemoryContext
)

__all__ = [
    "GraphMemory",
    "VectorMemory", 
    "HybridMemorySystem",
    "MemoryNode",
    "MemoryRelationship",
    "EmbeddingModel",
    "MemoryType",
    "EntityType", 
    "RelationshipType",
    "MemoryQuery",
    "MemoryResult",
    "MemoryContext"
]