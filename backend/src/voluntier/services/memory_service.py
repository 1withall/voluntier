"""
Memory service for managing hybrid memory system operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..memory import (
    HybridMemorySystem, GraphMemory, VectorMemory, EmbeddingModel,
    EntityType, RelationshipType, MemoryType, MemoryQuery, 
    MemoryResult, MemoryContext, EmbeddingRequest
)
from ..config import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for managing the hybrid memory system operations.
    
    Provides high-level interfaces for:
    - Entity lifecycle management
    - Relationship management  
    - Contextual search and retrieval
    - Memory analytics and maintenance
    """
    
    def __init__(self):
        self.memory_system: Optional[HybridMemorySystem] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the hybrid memory system."""
        if self._initialized:
            return
        
        try:
            # Create embedding model configuration
            embedding_model = EmbeddingModel(
                name=settings.memory.embedding_model_name,
                dimension=settings.memory.embedding_dimension,
                model_type=settings.memory.embedding_model_type
            )
            
            # Initialize graph memory
            graph_memory = GraphMemory(
                uri=settings.neo4j.uri,
                username=settings.neo4j.user,
                password=settings.neo4j.password
            )
            
            # Initialize vector memory
            vector_memory = VectorMemory(
                embedding_model=embedding_model,
                index_path=settings.memory.vector_index_path,
                metadata_path=settings.memory.vector_metadata_path
            )
            
            # Create hybrid system
            self.memory_system = HybridMemorySystem(
                graph_memory=graph_memory,
                vector_memory=vector_memory
            )
            
            # Initialize the system
            await self.memory_system.initialize()
            
            self._initialized = True
            logger.info("Memory service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the memory service."""
        if self.memory_system:
            await self.memory_system.close()
        self._initialized = False
    
    # Entity Management
    
    async def create_volunteer_profile(
        self,
        volunteer_id: str,
        profile_data: Dict[str, Any],
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Create a volunteer profile in memory."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_entity(
            entity_id=volunteer_id,
            entity_type=EntityType.VOLUNTEER,
            properties=profile_data,
            memory_type=MemoryType.SEMANTIC,
            context=context
        )
    
    async def create_organization_profile(
        self,
        organization_id: str,
        profile_data: Dict[str, Any],
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Create an organization profile in memory."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_entity(
            entity_id=organization_id,
            entity_type=EntityType.ORGANIZATION,
            properties=profile_data,
            memory_type=MemoryType.SEMANTIC,
            context=context
        )
    
    async def create_event_record(
        self,
        event_id: str,
        event_data: Dict[str, Any],
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Create an event record in memory."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_entity(
            entity_id=event_id,
            entity_type=EntityType.EVENT,
            properties=event_data,
            memory_type=MemoryType.EPISODIC,
            context=context
        )
    
    async def update_entity_profile(
        self,
        entity_id: str,
        updates: Dict[str, Any],
        text_content: Optional[str] = None,
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Update an entity profile."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.update_entity(
            entity_id=entity_id,
            properties=updates,
            text_content=text_content,
            context=context
        )
    
    # Relationship Management
    
    async def register_volunteer_for_event(
        self,
        volunteer_id: str,
        event_id: str,
        registration_data: Optional[Dict[str, Any]] = None,
        context: Optional[MemoryContext] = None
    ) -> Any:
        """Record volunteer registration for an event."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_relationship(
            source_id=volunteer_id,
            target_id=event_id,
            relationship_type=RelationshipType.REGISTERED_FOR,
            properties=registration_data or {},
            context=context
        )
    
    async def record_event_attendance(
        self,
        volunteer_id: str,
        event_id: str,
        attendance_data: Optional[Dict[str, Any]] = None,
        context: Optional[MemoryContext] = None
    ) -> Any:
        """Record volunteer attendance at an event."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_relationship(
            source_id=volunteer_id,
            target_id=event_id,
            relationship_type=RelationshipType.ATTENDED,
            properties=attendance_data or {},
            weight=1.5,  # Higher weight for actual attendance
            context=context
        )
    
    async def record_skill_association(
        self,
        entity_id: str,
        skill_id: str,
        proficiency_level: Optional[str] = None,
        context: Optional[MemoryContext] = None
    ) -> Any:
        """Record skill association for an entity."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_relationship(
            source_id=entity_id,
            target_id=skill_id,
            relationship_type=RelationshipType.HAS_SKILL,
            properties={"proficiency_level": proficiency_level} if proficiency_level else {},
            context=context
        )
    
    async def record_collaboration(
        self,
        entity1_id: str,
        entity2_id: str,
        collaboration_data: Optional[Dict[str, Any]] = None,
        context: Optional[MemoryContext] = None
    ) -> Any:
        """Record collaboration between entities."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_relationship(
            source_id=entity1_id,
            target_id=entity2_id,
            relationship_type=RelationshipType.COLLABORATES_WITH,
            properties=collaboration_data or {},
            bidirectional=True,
            context=context
        )
    
    # Search and Retrieval
    
    async def search_volunteers(
        self,
        query_text: Optional[str] = None,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 10,
        context: Optional[MemoryContext] = None
    ) -> List[MemoryResult]:
        """Search for volunteers based on criteria."""
        if not self._initialized:
            await self.initialize()
        
        filters = {}
        if skills:
            filters["skills"] = skills
        if location:
            filters["location"] = location
        
        query = MemoryQuery(
            query_text=query_text,
            entity_types=[EntityType.VOLUNTEER],
            filters=filters,
            limit=limit,
            context=context
        )
        
        return await self.memory_system.contextual_search(query)
    
    async def search_events(
        self,
        query_text: Optional[str] = None,
        date_range: Optional[tuple] = None,
        location: Optional[str] = None,
        skills_required: Optional[List[str]] = None,
        limit: int = 10,
        context: Optional[MemoryContext] = None
    ) -> List[MemoryResult]:
        """Search for events based on criteria."""
        if not self._initialized:
            await self.initialize()
        
        filters = {}
        if location:
            filters["location"] = location
        if skills_required:
            filters["skills"] = skills_required
        if date_range:
            filters["date_start"] = date_range[0]
            filters["date_end"] = date_range[1]
        
        query = MemoryQuery(
            query_text=query_text,
            entity_types=[EntityType.EVENT],
            filters=filters,
            limit=limit,
            context=context
        )
        
        return await self.memory_system.contextual_search(query)
    
    async def find_similar_volunteers(
        self,
        volunteer_id: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        context: Optional[MemoryContext] = None
    ) -> List[str]:
        """Find volunteers similar to the given volunteer."""
        if not self._initialized:
            await self.initialize()
        
        similar_entities = await self.memory_system.vector_memory.get_similar_entities(
            entity_id=volunteer_id,
            limit=limit
        )
        
        # Filter by similarity threshold and entity type
        filtered_results = []
        for entity_id, score in similar_entities:
            if score >= similarity_threshold:
                # Verify it's a volunteer
                entity_query = MemoryQuery(
                    entity_types=[EntityType.VOLUNTEER],
                    filters={"id": entity_id},
                    limit=1
                )
                entities = await self.memory_system.graph_memory.find_entities(entity_query)
                if entities:
                    filtered_results.append(entity_id)
        
        return filtered_results
    
    async def get_volunteer_recommendations(
        self,
        event_id: str,
        limit: int = 10,
        context: Optional[MemoryContext] = None
    ) -> List[Dict[str, Any]]:
        """Get volunteer recommendations for an event."""
        if not self._initialized:
            await self.initialize()
        
        # Get event details
        event_query = MemoryQuery(
            entity_types=[EntityType.EVENT],
            filters={"id": event_id},
            limit=1
        )
        events = await self.memory_system.graph_memory.find_entities(event_query)
        
        if not events:
            return []
        
        event = events[0]
        event_skills = event.content.get("skills", [])
        event_location = event.content.get("location", "")
        
        # Search for volunteers with matching skills or in similar location
        volunteer_query = MemoryQuery(
            query_text=f"volunteer skills {' '.join(event_skills)} location {event_location}",
            entity_types=[EntityType.VOLUNTEER],
            filters={"skills": event_skills} if event_skills else {},
            limit=limit * 2,  # Get more for filtering
            context=context
        )
        
        volunteers = await self.memory_system.contextual_search(volunteer_query)
        
        # Convert to recommendation format with scores
        recommendations = []
        for volunteer in volunteers[:limit]:
            recommendations.append({
                "volunteer_id": volunteer.entity_id,
                "volunteer_data": volunteer.content,
                "match_score": volunteer.similarity_score or 0,
                "matching_skills": list(set(volunteer.content.get("skills", [])) & set(event_skills)),
                "reason": self._generate_recommendation_reason(volunteer, event)
            })
        
        return recommendations
    
    # Analytics and Insights
    
    async def get_entity_context(
        self,
        entity_id: str,
        context_depth: int = 2
    ) -> Dict[str, Any]:
        """Get comprehensive context for an entity."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.get_entity_context(
            entity_id=entity_id,
            context_depth=context_depth
        )
    
    async def get_community_insights(
        self,
        entity_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get community insights around an entity."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.graph_memory.get_community_insights(
            entity_id=entity_id,
            depth=depth
        )
    
    async def get_memory_analytics(self) -> Dict[str, Any]:
        """Get comprehensive memory system analytics."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.get_memory_analytics()
    
    # Workflow Integration
    
    async def record_workflow_execution(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Record workflow execution in memory."""
        if not self._initialized:
            await self.initialize()
        
        return await self.memory_system.create_entity(
            entity_id=workflow_id,
            entity_type=EntityType.WORKFLOW,
            properties=workflow_data,
            memory_type=MemoryType.PROCEDURAL,
            context=context
        )
    
    async def record_decision_point(
        self,
        decision_id: str,
        decision_data: Dict[str, Any],
        related_entities: Optional[List[str]] = None,
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Record a decision point in memory."""
        if not self._initialized:
            await self.initialize()
        
        # Create decision entity
        result = await self.memory_system.create_entity(
            entity_id=decision_id,
            entity_type=EntityType.DECISION,
            properties=decision_data,
            memory_type=MemoryType.CONTEXTUAL,
            context=context
        )
        
        # Link to related entities
        if related_entities:
            for entity_id in related_entities:
                try:
                    await self.memory_system.create_relationship(
                        source_id=decision_id,
                        target_id=entity_id,
                        relationship_type=RelationshipType.DEPENDS_ON,
                        properties={"decision_context": True},
                        context=context
                    )
                except Exception as e:
                    logger.warning(f"Failed to link decision {decision_id} to entity {entity_id}: {e}")
        
        return result
    
    # Helper Methods
    
    def _generate_recommendation_reason(
        self, 
        volunteer: MemoryResult, 
        event: MemoryResult
    ) -> str:
        """Generate a reason for recommending a volunteer for an event."""
        volunteer_skills = set(volunteer.content.get("skills", []))
        event_skills = set(event.content.get("skills", []))
        matching_skills = volunteer_skills & event_skills
        
        reasons = []
        
        if matching_skills:
            reasons.append(f"Has relevant skills: {', '.join(list(matching_skills)[:3])}")
        
        if volunteer.similarity_score and volunteer.similarity_score > 0.8:
            reasons.append("High compatibility score")
        
        volunteer_location = volunteer.content.get("location", "")
        event_location = event.content.get("location", "")
        if volunteer_location and event_location and volunteer_location == event_location:
            reasons.append("Same location")
        
        if not reasons:
            reasons.append("General profile match")
        
        return "; ".join(reasons)