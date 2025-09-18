"""
FAISS vector memory implementation for efficient similarity search and contextual retrieval.
"""

import asyncio
import logging
import pickle
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

import faiss
import openai
from sentence_transformers import SentenceTransformer

from .memory_types import (
    EntityType, MemoryType, MemoryQuery, MemoryResult, 
    MemoryContext, EmbeddingRequest
)
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingModel:
    """Configuration for embedding model."""
    name: str
    dimension: int
    model_type: str  # 'openai', 'sentence_transformer', 'custom'
    max_tokens: Optional[int] = None
    model_instance: Optional[Any] = None


@dataclass
class VectorEntry:
    """Represents a vector entry in the FAISS index."""
    entity_id: str
    entity_type: EntityType
    memory_type: MemoryType
    embedding: np.ndarray
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class VectorMemory:
    """
    FAISS-based vector memory for efficient similarity search and contextual retrieval.
    
    Handles:
    - Text embedding generation
    - Vector storage and indexing
    - Similarity search
    - Contextual retrieval
    - Dynamic index updates
    """
    
    def __init__(
        self, 
        embedding_model: EmbeddingModel,
        index_path: str = "./data/vector_index",
        metadata_path: str = "./data/vector_metadata.pkl"
    ):
        self.embedding_model = embedding_model
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        
        # FAISS index and metadata storage
        self.index: Optional[faiss.Index] = None
        self.metadata: Dict[int, VectorEntry] = {}
        self.entity_to_index: Dict[str, List[int]] = {}
        
        # Concurrency control
        self._lock = asyncio.Lock()
        self._next_id = 0
        
        # Initialize embedding model
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self) -> None:
        """Initialize the embedding model based on configuration."""
        if self.embedding_model.model_type == "openai":
            openai.api_key = settings.openai_api_key
            self.embedding_model.model_instance = None  # Use API directly
            
        elif self.embedding_model.model_type == "sentence_transformer":
            self.embedding_model.model_instance = SentenceTransformer(
                self.embedding_model.name
            )
            
        else:
            raise ValueError(f"Unsupported embedding model type: {self.embedding_model.model_type}")
    
    async def initialize(self) -> None:
        """Initialize FAISS index and load existing data."""
        try:
            # Create directories if they don't exist
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize or load FAISS index
            if self.index_path.exists():
                await self._load_index()
            else:
                await self._create_new_index()
            
            logger.info(f"Vector memory initialized with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")
            raise
    
    async def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        # Use IndexFlatIP for inner product similarity (cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_model.dimension)
        
        # Wrap with IDMap for dynamic additions/deletions
        self.index = faiss.IndexIDMap(self.index)
        
        await self._save_index()
    
    async def _load_index(self) -> None:
        """Load existing FAISS index and metadata."""
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))
        
        # Load metadata
        if self.metadata_path.exists():
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data.get("metadata", {})
                self.entity_to_index = data.get("entity_to_index", {})
                self._next_id = data.get("next_id", 0)
    
    async def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        with open(self.metadata_path, 'wb') as f:
            pickle.dump({
                "metadata": self.metadata,
                "entity_to_index": self.entity_to_index,
                "next_id": self._next_id
            }, f)
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for given text."""
        if self.embedding_model.model_type == "openai":
            response = await openai.Embedding.acreate(
                model=self.embedding_model.name,
                input=text
            )
            embedding = np.array(response['data'][0]['embedding'], dtype=np.float32)
            
        elif self.embedding_model.model_type == "sentence_transformer":
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embedding_model.model_instance.encode, 
                text
            )
            embedding = embedding.astype(np.float32)
            
        else:
            raise ValueError(f"Unsupported model type: {self.embedding_model.model_type}")
        
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    async def add_embedding(self, request: EmbeddingRequest) -> int:
        """Add a new embedding to the vector store."""
        async with self._lock:
            # Generate embedding
            embedding = await self.generate_embedding(request.text)
            
            # Create vector entry
            vector_entry = VectorEntry(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                memory_type=request.memory_type,
                embedding=embedding,
                text=request.text,
                metadata=request.metadata
            )
            
            # Add to FAISS index
            vector_id = self._next_id
            self.index.add_with_ids(
                embedding.reshape(1, -1), 
                np.array([vector_id], dtype=np.int64)
            )
            
            # Update metadata
            self.metadata[vector_id] = vector_entry
            
            if request.entity_id not in self.entity_to_index:
                self.entity_to_index[request.entity_id] = []
            self.entity_to_index[request.entity_id].append(vector_id)
            
            self._next_id += 1
            
            # Save periodically (every 10 additions)
            if self._next_id % 10 == 0:
                await self._save_index()
            
            return vector_id
    
    async def update_embedding(
        self, 
        entity_id: str, 
        new_text: str,
        memory_type: Optional[MemoryType] = None
    ) -> List[int]:
        """Update embeddings for an entity."""
        async with self._lock:
            if entity_id not in self.entity_to_index:
                return []
            
            updated_ids = []
            
            # Update all embeddings for this entity (or specific memory type)
            for vector_id in self.entity_to_index[entity_id]:
                if vector_id in self.metadata:
                    entry = self.metadata[vector_id]
                    
                    if memory_type is None or entry.memory_type == memory_type:
                        # Generate new embedding
                        new_embedding = await self.generate_embedding(new_text)
                        
                        # Update FAISS index
                        self.index.remove_ids(np.array([vector_id], dtype=np.int64))
                        self.index.add_with_ids(
                            new_embedding.reshape(1, -1),
                            np.array([vector_id], dtype=np.int64)
                        )
                        
                        # Update metadata
                        entry.embedding = new_embedding
                        entry.text = new_text
                        entry.timestamp = datetime.utcnow()
                        
                        updated_ids.append(vector_id)
            
            await self._save_index()
            return updated_ids
    
    async def remove_entity_embeddings(self, entity_id: str) -> int:
        """Remove all embeddings for an entity."""
        async with self._lock:
            if entity_id not in self.entity_to_index:
                return 0
            
            vector_ids = self.entity_to_index[entity_id]
            
            # Remove from FAISS index
            if vector_ids:
                self.index.remove_ids(np.array(vector_ids, dtype=np.int64))
            
            # Remove from metadata
            for vector_id in vector_ids:
                self.metadata.pop(vector_id, None)
            
            # Remove entity mapping
            del self.entity_to_index[entity_id]
            
            await self._save_index()
            return len(vector_ids)
    
    async def similarity_search(
        self, 
        query: MemoryQuery,
        context: Optional[MemoryContext] = None
    ) -> List[MemoryResult]:
        """Perform similarity search based on query."""
        if not query.query_text:
            return []
        
        # Generate query embedding
        query_embedding = await self.generate_embedding(query.query_text)
        
        # Perform search
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            query.limit * 2  # Get extra results for filtering
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # No more results
                break
                
            if score < query.similarity_threshold:
                continue
            
            if idx in self.metadata:
                entry = self.metadata[idx]
                
                # Apply filters
                if self._matches_filters(entry, query):
                    results.append(MemoryResult(
                        entity_id=entry.entity_id,
                        entity_type=entry.entity_type,
                        content={
                            "text": entry.text,
                            "memory_type": entry.memory_type.value,
                            **entry.metadata
                        },
                        similarity_score=float(score),
                        metadata={"source": "vector", "vector_id": idx},
                        timestamp=entry.timestamp
                    ))
        
        return results[:query.limit]
    
    async def get_entity_embeddings(self, entity_id: str) -> List[VectorEntry]:
        """Get all embeddings for a specific entity."""
        if entity_id not in self.entity_to_index:
            return []
        
        embeddings = []
        for vector_id in self.entity_to_index[entity_id]:
            if vector_id in self.metadata:
                embeddings.append(self.metadata[vector_id])
        
        return embeddings
    
    async def get_similar_entities(
        self, 
        entity_id: str, 
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Find entities most similar to the given entity."""
        if entity_id not in self.entity_to_index:
            return []
        
        # Get entity embeddings
        entity_embeddings = await self.get_entity_embeddings(entity_id)
        if not entity_embeddings:
            return []
        
        # Use the most recent embedding as query
        query_embedding = entity_embeddings[-1].embedding
        
        # Search for similar vectors
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1),
            limit * 3  # Get extra for filtering out self
        )
        
        similar_entities = []
        seen_entities = {entity_id}  # Exclude self
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                break
                
            if idx in self.metadata:
                entry = self.metadata[idx]
                if entry.entity_id not in seen_entities:
                    similar_entities.append((entry.entity_id, float(score)))
                    seen_entities.add(entry.entity_id)
                    
                    if len(similar_entities) >= limit:
                        break
        
        return similar_entities
    
    def _matches_filters(self, entry: VectorEntry, query: MemoryQuery) -> bool:
        """Check if vector entry matches query filters."""
        if query.entity_types and entry.entity_type not in query.entity_types:
            return False
        
        if query.memory_types and entry.memory_type not in query.memory_types:
            return False
        
        if query.filters:
            for key, value in query.filters.items():
                if key in entry.metadata:
                    entry_value = entry.metadata[key]
                    if isinstance(value, list):
                        if entry_value not in value:
                            return False
                    else:
                        if entry_value != value:
                            return False
        
        return True
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector memory system."""
        total_vectors = self.index.ntotal if self.index else 0
        
        # Count by entity type and memory type
        entity_type_counts = {}
        memory_type_counts = {}
        
        for entry in self.metadata.values():
            entity_type_counts[entry.entity_type.value] = entity_type_counts.get(entry.entity_type.value, 0) + 1
            memory_type_counts[entry.memory_type.value] = memory_type_counts.get(entry.memory_type.value, 0) + 1
        
        return {
            "total_vectors": total_vectors,
            "total_entities": len(self.entity_to_index),
            "entity_type_distribution": entity_type_counts,
            "memory_type_distribution": memory_type_counts,
            "index_size_mb": self.index_path.stat().st_size / (1024 * 1024) if self.index_path.exists() else 0
        }