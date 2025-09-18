"""
Hybrid memory system combining Neo4j graph database and FAISS vector search.

This module provides a unified interface for managing community relationships,
volunteer interactions, and contextual information across the platform.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .graph_memory import GraphMemory, MemoryNode, MemoryRelationship
from .vector_memory import VectorMemory, EmbeddingModel, VectorEntry
from .memory_types import (
    EntityType, RelationshipType, MemoryType, MemoryQuery, 
    MemoryResult, MemoryContext, EmbeddingRequest, GraphUpdateRequest
)
from ..config import settings

logger = logging.getLogger(__name__)


class HybridMemorySystem:
    """
    Unified hybrid memory system combining graph and vector storage.
    
    Provides:
    - Unified entity management across graph and vector stores
    - Contextual retrieval combining structural and semantic information
    - Real-time updates with consistency across both systems
    - Scalable architecture for growing community data
    - Advanced querying combining graph traversal and similarity search
    """
    
    def __init__(
        self,
        graph_memory: GraphMemory,
        vector_memory: VectorMemory
    ):
        self.graph_memory = graph_memory
        self.vector_memory = vector_memory
        self._sync_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize both memory systems."""
        await asyncio.gather(
            self.graph_memory.initialize(),
            self.vector_memory.initialize()
        )
        logger.info("Hybrid memory system initialized successfully")
    
    async def close(self) -> None:
        """Close both memory systems."""
        await asyncio.gather(
            self.graph_memory.close(),
            self.vector_memory._save_index()
        )
    
    async def create_entity(
        self,
        entity_id: str,
        entity_type: EntityType,
        properties: Dict[str, Any],
        text_content: Optional[str] = None,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """
        Create an entity in both graph and vector stores.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (volunteer, organization, event, etc.)
            properties: Structured properties for graph storage
            text_content: Text content for vector embedding (auto-generated if None)
            memory_type: Type of memory for vector storage
            context: Context information for the operation
        
        Returns:
            Dictionary containing creation results from both systems
        """
        async with self._sync_lock:
            results = {}
            
            try:
                # Create entity in graph
                graph_node = await self.graph_memory.create_or_update_entity(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    properties=properties,
                    context=context
                )
                results["graph"] = graph_node
                
                # Generate text content if not provided
                if text_content is None:
                    text_content = self._generate_text_content(entity_type, properties)
                
                # Create embedding in vector store
                if text_content:
                    embedding_request = EmbeddingRequest(
                        text=text_content,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        memory_type=memory_type,
                        metadata={
                            "created_from": "hybrid_system",
                            "has_graph_node": True,
                            **properties
                        }
                    )
                    
                    vector_id = await self.vector_memory.add_embedding(embedding_request)
                    results["vector"] = {"vector_id": vector_id, "text": text_content}
                
                logger.info(f"Created entity {entity_id} in hybrid memory system")
                return results
                
            except Exception as e:
                logger.error(f"Failed to create entity {entity_id}: {e}")
                # Attempt cleanup if partial creation occurred
                await self._cleanup_partial_entity(entity_id, results)
                raise
    
    async def update_entity(
        self,
        entity_id: str,
        properties: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """Update an entity in both graph and vector stores."""
        async with self._sync_lock:
            results = {}
            
            try:
                # Update graph properties if provided
                if properties:
                    # Get current entity to preserve type
                    current_entities = await self.graph_memory.find_entities(
                        MemoryQuery(filters={"id": entity_id}, limit=1)
                    )
                    
                    if current_entities:
                        entity_type = current_entities[0].entity_type
                        graph_node = await self.graph_memory.create_or_update_entity(
                            entity_id=entity_id,
                            entity_type=entity_type,
                            properties=properties,
                            context=context
                        )
                        results["graph"] = graph_node
                
                # Update vector embeddings if text content provided
                if text_content:
                    updated_ids = await self.vector_memory.update_embedding(
                        entity_id=entity_id,
                        new_text=text_content,
                        memory_type=memory_type
                    )
                    results["vector"] = {"updated_vector_ids": updated_ids}
                
                logger.info(f"Updated entity {entity_id} in hybrid memory system")
                return results
                
            except Exception as e:
                logger.error(f"Failed to update entity {entity_id}: {e}")
                raise
    
    async def delete_entity(self, entity_id: str) -> Dict[str, Any]:
        """Delete an entity from both graph and vector stores."""
        async with self._sync_lock:
            results = {}
            
            try:
                # Remove from vector store
                removed_vectors = await self.vector_memory.remove_entity_embeddings(entity_id)
                results["vector"] = {"removed_vectors": removed_vectors}
                
                # Note: Graph deletion would require more complex logic to handle relationships
                # For now, we mark as deleted in properties
                await self.graph_memory.create_or_update_entity(
                    entity_id=entity_id,
                    entity_type=EntityType.VOLUNTEER,  # Placeholder, should get from existing
                    properties={"deleted": True, "deleted_at": datetime.utcnow().isoformat()}
                )
                results["graph"] = {"marked_deleted": True}
                
                logger.info(f"Deleted entity {entity_id} from hybrid memory system")
                return results
                
            except Exception as e:
                logger.error(f"Failed to delete entity {entity_id}: {e}")
                raise
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        bidirectional: bool = False,
        context: Optional[MemoryContext] = None
    ) -> MemoryRelationship:
        """Create a relationship in the graph store."""
        request = GraphUpdateRequest(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            weight=weight,
            bidirectional=bidirectional
        )
        
        return await self.graph_memory.create_relationship(request, context)
    
    async def contextual_search(
        self,
        query: MemoryQuery,
        combine_strategies: List[str] = ["merge", "rerank"],
        context: Optional[MemoryContext] = None
    ) -> List[MemoryResult]:
        """
        Perform contextual search combining graph and vector results.
        
        Args:
            query: Search query with parameters
            combine_strategies: List of strategies for combining results
            context: Context information for the search
        
        Returns:
            Combined and ranked results from both systems
        """
        results = {}
        
        # Perform parallel searches
        search_tasks = []
        
        # Vector similarity search
        if query.query_text:
            search_tasks.append(
                self._vector_search_with_label(query, context)
            )
        
        # Graph-based search
        search_tasks.append(
            self._graph_search_with_label(query, context)
        )
        
        # Execute searches concurrently
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        vector_results = []
        graph_results = []
        
        for result in search_results:
            if isinstance(result, Exception):
                logger.error(f"Search error: {result}")
                continue
            
            source, data = result
            if source == "vector":
                vector_results = data
            elif source == "graph":
                graph_results = data
        
        # Combine results using specified strategies
        combined_results = self._combine_results(
            vector_results, 
            graph_results, 
            combine_strategies,
            query.limit
        )
        
        return combined_results
    
    async def get_entity_context(
        self,
        entity_id: str,
        context_depth: int = 2,
        include_similar: bool = True,
        similarity_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for an entity including relationships and similar entities.
        
        Args:
            entity_id: Entity to get context for
            context_depth: Depth of relationship traversal
            include_similar: Whether to include similar entities from vector store
            similarity_limit: Number of similar entities to include
        
        Returns:
            Dictionary containing entity context, relationships, and similar entities
        """
        context_data = {
            "entity_id": entity_id,
            "graph_context": {},
            "vector_context": {},
            "similar_entities": [],
            "community_insights": {}
        }
        
        try:
            # Get graph context
            community_insights = await self.graph_memory.get_community_insights(
                entity_id, depth=context_depth
            )
            context_data["community_insights"] = community_insights
            
            # Get vector embeddings for the entity
            vector_embeddings = await self.vector_memory.get_entity_embeddings(entity_id)
            context_data["vector_context"] = {
                "embeddings_count": len(vector_embeddings),
                "memory_types": list(set(e.memory_type.value for e in vector_embeddings)),
                "latest_text": vector_embeddings[-1].text if vector_embeddings else None
            }
            
            # Get similar entities if requested
            if include_similar:
                similar_entities = await self.vector_memory.get_similar_entities(
                    entity_id, limit=similarity_limit
                )
                context_data["similar_entities"] = similar_entities
            
            return context_data
            
        except Exception as e:
            logger.error(f"Failed to get entity context for {entity_id}: {e}")
            return context_data
    
    async def get_memory_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics about the hybrid memory system."""
        try:
            # Get vector statistics
            vector_stats = await self.vector_memory.get_memory_statistics()
            
            # Get basic graph statistics (would need to implement in GraphMemory)
            # For now, return vector stats with placeholder graph stats
            graph_stats = {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_type_distribution": {},
                "relationship_type_distribution": {}
            }
            
            return {
                "vector_memory": vector_stats,
                "graph_memory": graph_stats,
                "system_health": {
                    "vector_available": self.vector_memory.index is not None,
                    "graph_available": self.graph_memory.driver is not None,
                    "last_sync": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory analytics: {e}")
            return {"error": str(e)}
    
    # Helper methods
    
    async def _vector_search_with_label(
        self, 
        query: MemoryQuery, 
        context: Optional[MemoryContext]
    ) -> tuple[str, List[MemoryResult]]:
        """Perform vector search with source label."""
        try:
            results = await self.vector_memory.similarity_search(query, context)
            return ("vector", results)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return ("vector", [])
    
    async def _graph_search_with_label(
        self, 
        query: MemoryQuery, 
        context: Optional[MemoryContext]
    ) -> tuple[str, List[MemoryResult]]:
        """Perform graph search with source label."""
        try:
            results = await self.graph_memory.find_entities(query, context)
            return ("graph", results)
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return ("graph", [])
    
    def _combine_results(
        self,
        vector_results: List[MemoryResult],
        graph_results: List[MemoryResult],
        strategies: List[str],
        limit: int
    ) -> List[MemoryResult]:
        """Combine results from vector and graph searches."""
        # Simple merging strategy - deduplicate by entity_id and combine scores
        entity_results = {}
        
        # Add vector results
        for result in vector_results:
            entity_id = result.entity_id
            if entity_id not in entity_results:
                entity_results[entity_id] = result
            else:
                # Combine with existing result
                existing = entity_results[entity_id]
                existing.similarity_score = max(
                    existing.similarity_score or 0,
                    result.similarity_score or 0
                )
                existing.metadata.update(result.metadata)
        
        # Add graph results
        for result in graph_results:
            entity_id = result.entity_id
            if entity_id not in entity_results:
                entity_results[entity_id] = result
            else:
                # Enhance existing result with graph relationships
                existing = entity_results[entity_id]
                existing.relationships.extend(result.relationships)
                existing.metadata.update(result.metadata)
        
        # Sort by combined score (similarity + relationship count)
        combined_results = list(entity_results.values())
        for result in combined_results:
            relationship_score = len(result.relationships) * 0.1  # Weight relationships
            total_score = (result.similarity_score or 0) + relationship_score
            result.similarity_score = total_score
        
        # Sort and limit
        combined_results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        return combined_results[:limit]
    
    def _generate_text_content(
        self, 
        entity_type: EntityType, 
        properties: Dict[str, Any]
    ) -> str:
        """Generate text content for vector embedding from entity properties."""
        if entity_type == EntityType.VOLUNTEER:
            return f"""
            Volunteer: {properties.get('name', 'Unknown')}
            Skills: {', '.join(properties.get('skills', []))}
            Interests: {', '.join(properties.get('interests', []))}
            Location: {properties.get('location', 'Not specified')}
            Experience: {properties.get('experience_description', '')}
            """.strip()
        
        elif entity_type == EntityType.ORGANIZATION:
            return f"""
            Organization: {properties.get('name', 'Unknown')}
            Description: {properties.get('description', '')}
            Focus Areas: {', '.join(properties.get('focus_areas', []))}
            Location: {properties.get('location', 'Not specified')}
            """.strip()
        
        elif entity_type == EntityType.EVENT:
            return f"""
            Event: {properties.get('title', 'Unknown')}
            Description: {properties.get('description', '')}
            Skills Required: {', '.join(properties.get('skills', []))}
            Location: {properties.get('location', 'Not specified')}
            Date: {properties.get('date', 'Not specified')}
            """.strip()
        
        else:
            # Generic text generation for other entity types
            text_parts = [f"{entity_type.value.title()}: {properties.get('name', 'Unknown')}"]
            
            if 'description' in properties:
                text_parts.append(f"Description: {properties['description']}")
            
            for key, value in properties.items():
                if key not in ['name', 'description', 'id']:
                    if isinstance(value, list):
                        text_parts.append(f"{key.title()}: {', '.join(map(str, value))}")
                    else:
                        text_parts.append(f"{key.title()}: {value}")
            
            return '\n'.join(text_parts)
    
    async def _cleanup_partial_entity(
        self, 
        entity_id: str, 
        partial_results: Dict[str, Any]
    ) -> None:
        """Clean up partially created entity in case of failure."""
        try:
            if "vector" in partial_results:
                await self.vector_memory.remove_entity_embeddings(entity_id)
            
            # Graph cleanup would be more complex - for now just log
            if "graph" in partial_results:
                logger.warning(f"Graph entity {entity_id} may need manual cleanup")
                
        except Exception as e:
            logger.error(f"Failed to cleanup partial entity {entity_id}: {e}")