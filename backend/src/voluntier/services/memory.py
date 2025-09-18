"""Memory service using Neo4j and FAISS for contextual memory."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import neo4j
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from voluntier.config import settings
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class MemoryService:
    """Service for managing agent memory using Neo4j and FAISS."""
    
    def __init__(self):
        self.neo4j_driver = neo4j.AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password),
            database=settings.neo4j.database,
        )
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS index
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        self.memory_store = {}  # In-memory store for FAISS index mapping
        
    async def store_decision_context(
        self,
        context: Dict[str, Any],
        decision: Dict[str, Any],
        timestamp: datetime,
    ) -> str:
        """
        Store decision context in memory.
        
        Args:
            context: Decision context
            decision: Decision made
            timestamp: When the decision was made
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        
        try:
            # Create text representation for embedding
            text_content = f"""
            Context: {json.dumps(context)}
            Decision: {decision['recommended_action']}
            Reasoning: {decision.get('reasoning', '')}
            Confidence: {decision.get('confidence', 0)}
            """
            
            # Generate embedding
            embedding = self.encoder.encode([text_content])[0]
            
            # Store in FAISS
            self.faiss_index.add(np.array([embedding], dtype=np.float32))
            self.memory_store[self.faiss_index.ntotal - 1] = {
                "memory_id": memory_id,
                "type": "decision_context",
                "context": context,
                "decision": decision,
                "timestamp": timestamp.isoformat(),
                "text_content": text_content,
            }
            
            # Store in Neo4j
            async with self.neo4j_driver.session() as session:
                await session.execute_write(
                    self._create_decision_node,
                    memory_id=memory_id,
                    context=context,
                    decision=decision,
                    timestamp=timestamp,
                )
            
            logger.info(f"Stored decision context: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store decision context: {str(e)}")
            raise
    
    async def store_execution_result(
        self,
        action: str,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        timestamp: datetime,
    ) -> str:
        """
        Store execution result in memory.
        
        Args:
            action: Action that was executed
            context: Execution context
            parameters: Action parameters
            result: Execution result
            timestamp: When the execution occurred
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        
        try:
            # Create text representation
            text_content = f"""
            Action: {action}
            Context: {json.dumps(context)}
            Parameters: {json.dumps(parameters)}
            Result: {json.dumps(result)}
            Success: {result.get('success', False)}
            """
            
            # Generate embedding
            embedding = self.encoder.encode([text_content])[0]
            
            # Store in FAISS
            self.faiss_index.add(np.array([embedding], dtype=np.float32))
            self.memory_store[self.faiss_index.ntotal - 1] = {
                "memory_id": memory_id,
                "type": "execution_result",
                "action": action,
                "context": context,
                "parameters": parameters,
                "result": result,
                "timestamp": timestamp.isoformat(),
                "text_content": text_content,
            }
            
            # Store in Neo4j
            async with self.neo4j_driver.session() as session:
                await session.execute_write(
                    self._create_execution_node,
                    memory_id=memory_id,
                    action=action,
                    context=context,
                    parameters=parameters,
                    result=result,
                    timestamp=timestamp,
                )
            
            logger.info(f"Stored execution result: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store execution result: {str(e)}")
            raise
    
    async def store_learning_data(
        self,
        action: str,
        context: Dict[str, Any],
        outcome: Dict[str, Any],
        insights: List[str],
        timestamp: datetime,
    ) -> str:
        """
        Store learning data in memory.
        
        Args:
            action: Action that was learned from
            context: Learning context
            outcome: Actual outcome
            insights: Learning insights
            timestamp: When the learning occurred
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        
        try:
            # Create text representation
            text_content = f"""
            Action: {action}
            Context: {json.dumps(context)}
            Outcome: {json.dumps(outcome)}
            Insights: {'; '.join(insights)}
            """
            
            # Generate embedding
            embedding = self.encoder.encode([text_content])[0]
            
            # Store in FAISS
            self.faiss_index.add(np.array([embedding], dtype=np.float32))
            self.memory_store[self.faiss_index.ntotal - 1] = {
                "memory_id": memory_id,
                "type": "learning_data",
                "action": action,
                "context": context,
                "outcome": outcome,
                "insights": insights,
                "timestamp": timestamp.isoformat(),
                "text_content": text_content,
            }
            
            # Store in Neo4j
            async with self.neo4j_driver.session() as session:
                await session.execute_write(
                    self._create_learning_node,
                    memory_id=memory_id,
                    action=action,
                    context=context,
                    outcome=outcome,
                    insights=insights,
                    timestamp=timestamp,
                )
            
            logger.info(f"Stored learning data: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store learning data: {str(e)}")
            raise
    
    async def get_relevant_context(
        self,
        query: str,
        limit: int = 10,
        include_related: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get relevant context for a query.
        
        Args:
            query: Query string
            limit: Maximum number of results
            include_related: Whether to include related context
            
        Returns:
            List of relevant context items
        """
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0]
            
            # Search FAISS index
            if self.faiss_index.ntotal == 0:
                return []
            
            # Get top k similar items
            distances, indices = self.faiss_index.search(
                np.array([query_embedding], dtype=np.float32),
                min(limit, self.faiss_index.ntotal)
            )
            
            # Retrieve matching items
            relevant_items = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx in self.memory_store:
                    item = self.memory_store[idx].copy()
                    item["similarity_score"] = 1.0 / (1.0 + distances[0][i])  # Convert distance to similarity
                    relevant_items.append(item)
            
            # If include_related, also get related items from Neo4j
            if include_related and relevant_items:
                memory_ids = [item["memory_id"] for item in relevant_items[:5]]  # Top 5 for related search
                related_items = await self._get_related_memories(memory_ids)
                
                # Add related items that aren't already included
                existing_ids = {item["memory_id"] for item in relevant_items}
                for related_item in related_items:
                    if related_item["memory_id"] not in existing_ids:
                        relevant_items.append(related_item)
            
            # Sort by similarity and return top results
            relevant_items.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            return relevant_items[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {str(e)}")
            return []
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user-specific context.
        
        Args:
            user_id: User ID
            
        Returns:
            User context
        """
        try:
            async with self.neo4j_driver.session() as session:
                result = await session.execute_read(
                    self._get_user_context_query,
                    user_id=user_id,
                )
                return result
        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            return {}
    
    async def _get_related_memories(self, memory_ids: List[str]) -> List[Dict[str, Any]]:
        """Get memories related to the given memory IDs."""
        try:
            async with self.neo4j_driver.session() as session:
                result = await session.execute_read(
                    self._get_related_memories_query,
                    memory_ids=memory_ids,
                )
                return result
        except Exception as e:
            logger.error(f"Failed to get related memories: {str(e)}")
            return []
    
    @staticmethod
    async def _create_decision_node(tx, memory_id: str, context: Dict[str, Any], decision: Dict[str, Any], timestamp: datetime):
        """Create a decision node in Neo4j."""
        query = """
        CREATE (d:Decision {
            memory_id: $memory_id,
            action: $action,
            confidence: $confidence,
            reasoning: $reasoning,
            timestamp: $timestamp,
            context: $context
        })
        """
        await tx.run(
            query,
            memory_id=memory_id,
            action=decision.get("recommended_action"),
            confidence=decision.get("confidence", 0),
            reasoning=decision.get("reasoning", ""),
            timestamp=timestamp.isoformat(),
            context=json.dumps(context),
        )
    
    @staticmethod
    async def _create_execution_node(tx, memory_id: str, action: str, context: Dict[str, Any], parameters: Dict[str, Any], result: Dict[str, Any], timestamp: datetime):
        """Create an execution node in Neo4j."""
        query = """
        CREATE (e:Execution {
            memory_id: $memory_id,
            action: $action,
            success: $success,
            timestamp: $timestamp,
            context: $context,
            parameters: $parameters,
            result: $result
        })
        """
        await tx.run(
            query,
            memory_id=memory_id,
            action=action,
            success=result.get("success", False),
            timestamp=timestamp.isoformat(),
            context=json.dumps(context),
            parameters=json.dumps(parameters),
            result=json.dumps(result),
        )
    
    @staticmethod
    async def _create_learning_node(tx, memory_id: str, action: str, context: Dict[str, Any], outcome: Dict[str, Any], insights: List[str], timestamp: datetime):
        """Create a learning node in Neo4j."""
        query = """
        CREATE (l:Learning {
            memory_id: $memory_id,
            action: $action,
            timestamp: $timestamp,
            context: $context,
            outcome: $outcome,
            insights: $insights
        })
        """
        await tx.run(
            query,
            memory_id=memory_id,
            action=action,
            timestamp=timestamp.isoformat(),
            context=json.dumps(context),
            outcome=json.dumps(outcome),
            insights=insights,
        )
    
    @staticmethod
    async def _get_user_context_query(tx, user_id: str):
        """Get user context from Neo4j."""
        query = """
        MATCH (u:User {id: $user_id})
        OPTIONAL MATCH (u)-[:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (u)-[:HAS_INTEREST]->(i:Interest)
        OPTIONAL MATCH (u)-[:ATTENDED]->(e:Event)
        RETURN {
            user_id: u.id,
            skills: collect(DISTINCT s.name),
            interests: collect(DISTINCT i.name),
            events_attended: count(DISTINCT e),
            verification_status: u.verification_status,
            trust_score: u.trust_score
        } as context
        """
        result = await tx.run(query, user_id=user_id)
        record = await result.single()
        return record["context"] if record else {}
    
    @staticmethod
    async def _get_related_memories_query(tx, memory_ids: List[str]):
        """Get related memories from Neo4j."""
        query = """
        MATCH (m1) WHERE m1.memory_id IN $memory_ids
        MATCH (m1)-[:RELATED_TO]-(m2)
        WHERE NOT m2.memory_id IN $memory_ids
        RETURN {
            memory_id: m2.memory_id,
            type: labels(m2)[0],
            similarity_score: 0.8
        } as memory
        LIMIT 10
        """
        result = await tx.run(query, memory_ids=memory_ids)
        return [record["memory"] async for record in result]
    
    async def close(self):
        """Close connections."""
        await self.neo4j_driver.close()