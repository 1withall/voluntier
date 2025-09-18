"""
Neo4j graph memory implementation for managing entity relationships and community structure.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import Neo4jError

from .memory_types import (
    EntityType, RelationshipType, MemoryQuery, MemoryResult, 
    MemoryContext, GraphUpdateRequest
)
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryNode:
    """Represents a node in the graph memory system."""
    id: str
    entity_type: EntityType
    properties: Dict[str, Any]
    labels: Set[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class MemoryRelationship:
    """Represents a relationship in the graph memory system."""
    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    weight: float
    created_at: datetime
    updated_at: datetime


class GraphMemory:
    """
    Neo4j-based graph memory for managing entity relationships and community structure.
    
    Handles:
    - Entity storage and retrieval
    - Relationship management
    - Community detection and analysis
    - Path finding and graph traversal
    - Real-time graph updates
    """
    
    def __init__(self, uri: str, username: str, password: str):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: Optional[AsyncDriver] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize Neo4j connection and create constraints/indexes."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            await self._create_constraints_and_indexes()
            logger.info("Graph memory system initialized successfully")
        except Neo4jError as e:
            logger.error(f"Failed to initialize graph memory: {e}")
            raise
    
    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
    
    async def _create_constraints_and_indexes(self) -> None:
        """Create necessary constraints and indexes for optimal performance."""
        constraints_and_indexes = [
            # Unique constraints for entity IDs
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT volunteer_id_unique IF NOT EXISTS FOR (v:Volunteer) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            
            # Indexes for common query patterns
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
            "CREATE INDEX entity_created_idx IF NOT EXISTS FOR (e:Entity) ON (e.created_at)",
            "CREATE INDEX volunteer_skills_idx IF NOT EXISTS FOR (v:Volunteer) ON (v.skills)",
            "CREATE INDEX event_date_idx IF NOT EXISTS FOR (e:Event) ON (e.date)",
            "CREATE INDEX location_area_idx IF NOT EXISTS FOR (l:Location) ON (l.area)",
            
            # Relationship indexes
            "CREATE INDEX rel_type_idx IF NOT EXISTS FOR ()-[r]-() ON (r.relationship_type)",
            "CREATE INDEX rel_weight_idx IF NOT EXISTS FOR ()-[r]-() ON (r.weight)",
            "CREATE INDEX rel_created_idx IF NOT EXISTS FOR ()-[r]-() ON (r.created_at)"
        ]
        
        async with self.driver.session() as session:
            for constraint_or_index in constraints_and_indexes:
                try:
                    await session.run(constraint_or_index)
                except Neo4jError as e:
                    # Constraint/index might already exist
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Failed to create constraint/index: {e}")
    
    async def create_or_update_entity(
        self, 
        entity_id: str, 
        entity_type: EntityType,
        properties: Dict[str, Any],
        context: Optional[MemoryContext] = None
    ) -> MemoryNode:
        """Create or update an entity in the graph."""
        async with self._lock:
            query = """
            MERGE (e:Entity {id: $entity_id})
            SET e.entity_type = $entity_type,
                e.updated_at = datetime(),
                e += $properties
            ON CREATE SET e.created_at = datetime()
            
            // Add specific label based on entity type
            WITH e
            CALL apoc.create.addLabels(e, [$entity_type]) YIELD node
            RETURN e
            """
            
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    entity_id=entity_id,
                    entity_type=entity_type.value,
                    properties=properties
                )
                
                record = await result.single()
                if record:
                    node_data = record["e"]
                    return MemoryNode(
                        id=node_data["id"],
                        entity_type=EntityType(node_data["entity_type"]),
                        properties=dict(node_data),
                        labels=set(node_data.labels),
                        created_at=node_data["created_at"],
                        updated_at=node_data["updated_at"]
                    )
                
                raise Exception(f"Failed to create/update entity {entity_id}")
    
    async def create_relationship(
        self, 
        request: GraphUpdateRequest,
        context: Optional[MemoryContext] = None
    ) -> MemoryRelationship:
        """Create or update a relationship between entities."""
        async with self._lock:
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            
            MERGE (source)-[r:RELATES {
                relationship_type: $relationship_type,
                source_id: $source_id,
                target_id: $target_id
            }]->(target)
            
            SET r.weight = $weight,
                r.updated_at = datetime(),
                r += $properties
            ON CREATE SET r.created_at = datetime()
            
            // Create bidirectional relationship if requested
            WITH source, target, r
            CALL CASE WHEN $bidirectional THEN
                apoc.do.when(
                    NOT EXISTS((target)-[:RELATES {relationship_type: $relationship_type}]->(source)),
                    "MERGE (target)-[r2:RELATES {
                        relationship_type: $relationship_type,
                        source_id: $target_id,
                        target_id: $source_id,
                        weight: $weight,
                        created_at: datetime(),
                        updated_at: datetime()
                    }]->(source)
                    SET r2 += $properties
                    RETURN r2",
                    "",
                    {target: target, source: source, relationship_type: $relationship_type, 
                     target_id: $target_id, source_id: $source_id, weight: $weight, properties: $properties}
                )
            ELSE
                ""
            END
            
            RETURN r
            """
            
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    source_id=request.source_id,
                    target_id=request.target_id,
                    relationship_type=request.relationship_type.value,
                    weight=request.weight,
                    properties=request.properties,
                    bidirectional=request.bidirectional
                )
                
                record = await result.single()
                if record:
                    rel_data = record["r"]
                    return MemoryRelationship(
                        id=str(rel_data.id),
                        source_id=rel_data["source_id"],
                        target_id=rel_data["target_id"],
                        relationship_type=RelationshipType(rel_data["relationship_type"]),
                        properties=dict(rel_data),
                        weight=rel_data["weight"],
                        created_at=rel_data["created_at"],
                        updated_at=rel_data["updated_at"]
                    )
                
                raise Exception(f"Failed to create relationship between {request.source_id} and {request.target_id}")
    
    async def find_entities(
        self, 
        query: MemoryQuery,
        context: Optional[MemoryContext] = None
    ) -> List[MemoryResult]:
        """Find entities based on query parameters."""
        cypher_query = self._build_entity_query(query)
        
        async with self.driver.session() as session:
            result = await session.run(cypher_query, **self._query_parameters(query))
            
            entities = []
            async for record in result:
                entity_data = record["e"]
                relationships = record.get("relationships", [])
                
                entities.append(MemoryResult(
                    entity_id=entity_data["id"],
                    entity_type=EntityType(entity_data["entity_type"]),
                    content=dict(entity_data),
                    relationships=relationships,
                    metadata={"source": "graph"},
                    timestamp=entity_data.get("updated_at", datetime.utcnow())
                ))
            
            return entities[:query.limit]
    
    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Dict[str, Any]]:
        """Find paths between two entities."""
        rel_filter = ""
        if relationship_types:
            rel_types = [rt.value for rt in relationship_types]
            rel_filter = f"WHERE ALL(r IN relationships(p) WHERE r.relationship_type IN {rel_types})"
        
        query = f"""
        MATCH p = (source:Entity {{id: $source_id}})-[*1..{max_depth}]-(target:Entity {{id: $target_id}})
        {rel_filter}
        RETURN p, length(p) as path_length
        ORDER BY path_length
        LIMIT 10
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            
            paths = []
            async for record in result:
                path = record["p"]
                path_data = {
                    "nodes": [dict(node) for node in path.nodes],
                    "relationships": [dict(rel) for rel in path.relationships],
                    "length": record["path_length"]
                }
                paths.append(path_data)
            
            return paths
    
    async def get_community_insights(
        self,
        entity_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get community insights for an entity."""
        query = f"""
        MATCH (center:Entity {{id: $entity_id}})
        OPTIONAL MATCH (center)-[r1*1..{depth}]-(connected:Entity)
        
        WITH center, collect(DISTINCT connected) as community
        
        // Calculate community metrics
        WITH center, community,
             size(community) as community_size,
             [entity IN community WHERE entity.entity_type = 'volunteer'] as volunteers,
             [entity IN community WHERE entity.entity_type = 'organization'] as organizations,
             [entity IN community WHERE entity.entity_type = 'event'] as events
        
        RETURN {{
            center_entity: center,
            community_size: community_size,
            volunteer_count: size(volunteers),
            organization_count: size(organizations),
            event_count: size(events),
            diversity_score: size(apoc.coll.toSet([entity IN community | entity.entity_type])) / 1.0
        }} as insights
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id)
            record = await result.single()
            
            if record:
                return record["insights"]
            return {}
    
    def _build_entity_query(self, query: MemoryQuery) -> str:
        """Build Cypher query from MemoryQuery."""
        base_query = "MATCH (e:Entity)"
        
        where_clauses = []
        
        if query.entity_types:
            entity_types = [et.value for et in query.entity_types]
            where_clauses.append(f"e.entity_type IN {entity_types}")
        
        if query.filters:
            for key, value in query.filters.items():
                if isinstance(value, list):
                    where_clauses.append(f"e.{key} IN {value}")
                else:
                    where_clauses.append(f"e.{key} = ${key}")
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add relationship collection
        base_query += """
        OPTIONAL MATCH (e)-[r:RELATES]-()
        WITH e, collect({
            type: r.relationship_type,
            target: CASE WHEN startNode(r) = e THEN endNode(r).id ELSE startNode(r).id END,
            weight: r.weight
        }) as relationships
        """
        
        base_query += " RETURN e, relationships ORDER BY e.updated_at DESC"
        
        return base_query
    
    def _query_parameters(self, query: MemoryQuery) -> Dict[str, Any]:
        """Extract query parameters for Cypher execution."""
        params = {}
        
        if query.filters:
            for key, value in query.filters.items():
                if not isinstance(value, list):
                    params[key] = value
        
        return params