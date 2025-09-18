"""
Memory system type definitions for the hybrid graph+vector architecture.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory storage and retrieval patterns."""
    EPISODIC = "episodic"  # Specific events and interactions
    SEMANTIC = "semantic"  # General knowledge and concepts
    PROCEDURAL = "procedural"  # Process and workflow knowledge
    CONTEXTUAL = "contextual"  # Situational awareness and state


class EntityType(str, Enum):
    """Types of entities stored in the memory system."""
    VOLUNTEER = "volunteer"
    ORGANIZATION = "organization"
    EVENT = "event"
    SKILL = "skill"
    LOCATION = "location"
    TASK = "task"
    RESOURCE = "resource"
    COMMUNITY = "community"
    WORKFLOW = "workflow"
    DECISION = "decision"


class RelationshipType(str, Enum):
    """Types of relationships between entities."""
    # Volunteer relationships
    REGISTERED_FOR = "registered_for"
    ATTENDED = "attended"
    COMPLETED = "completed"
    HAS_SKILL = "has_skill"
    LIVES_IN = "lives_in"
    MEMBER_OF = "member_of"
    
    # Organization relationships
    ORGANIZES = "organizes"
    LOCATED_IN = "located_in"
    REQUIRES_SKILL = "requires_skill"
    PROVIDES_RESOURCE = "provides_resource"
    
    # Event relationships
    REQUIRES = "requires"
    HAPPENS_AT = "happens_at"
    PRECEDES = "precedes"
    DEPENDS_ON = "depends_on"
    
    # Workflow relationships
    TRIGGERS = "triggers"
    EXECUTES = "executes"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    
    # Social relationships
    COLLABORATES_WITH = "collaborates_with"
    MENTORS = "mentors"
    RECOMMENDS = "recommends"
    TRUSTS = "trusts"


@dataclass
class MemoryContext:
    """Context information for memory operations."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryQuery(BaseModel):
    """Query structure for memory retrieval operations."""
    query_text: Optional[str] = None
    entity_types: Optional[List[EntityType]] = None
    relationship_types: Optional[List[RelationshipType]] = None
    memory_types: Optional[List[MemoryType]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    context: Optional[MemoryContext] = None


class MemoryResult(BaseModel):
    """Result structure for memory operations."""
    entity_id: str
    entity_type: EntityType
    content: Dict[str, Any]
    similarity_score: Optional[float] = None
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


@dataclass
class EmbeddingRequest:
    """Request for generating embeddings."""
    text: str
    entity_id: str
    entity_type: EntityType
    memory_type: MemoryType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphUpdateRequest:
    """Request for updating graph relationships."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    bidirectional: bool = False