"""
API endpoints for hybrid memory system operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.memory_service import MemoryService
from ..memory.memory_types import MemoryContext, EntityType, MemoryType
from ..dependencies import get_current_user
from ..models.auth import User

router = APIRouter(prefix="/memory", tags=["memory"])


# Pydantic models for request/response

class EntityCreationRequest(BaseModel):
    """Request model for creating entities."""
    entity_id: str
    entity_type: EntityType
    properties: Dict[str, Any]
    text_content: Optional[str] = None
    memory_type: MemoryType = MemoryType.SEMANTIC


class EntityUpdateRequest(BaseModel):
    """Request model for updating entities."""
    properties: Optional[Dict[str, Any]] = None
    text_content: Optional[str] = None


class RelationshipRequest(BaseModel):
    """Request model for creating relationships."""
    source_id: str
    target_id: str
    relationship_data: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Request model for memory searches."""
    query_text: Optional[str] = None
    entity_types: Optional[List[EntityType]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class MemoryAnalyticsResponse(BaseModel):
    """Response model for memory analytics."""
    vector_memory: Dict[str, Any]
    graph_memory: Dict[str, Any]
    system_health: Dict[str, Any]


class EntityContextResponse(BaseModel):
    """Response model for entity context."""
    entity_id: str
    graph_context: Dict[str, Any]
    vector_context: Dict[str, Any]
    similar_entities: List[tuple]
    community_insights: Dict[str, Any]


class RecommendationResponse(BaseModel):
    """Response model for volunteer recommendations."""
    volunteer_id: str
    volunteer_data: Dict[str, Any]
    match_score: float
    matching_skills: List[str]
    reason: str


# Dependency injection

async def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    service = MemoryService()
    await service.initialize()
    return service


def get_memory_context(current_user: User = Depends(get_current_user)) -> MemoryContext:
    """Create memory context from current user."""
    return MemoryContext(
        user_id=str(current_user.id),
        timestamp=datetime.utcnow(),
        metadata={"user_role": current_user.role}
    )


# Entity Management Endpoints

@router.post("/entities", summary="Create a new entity in memory")
async def create_entity(
    request: EntityCreationRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Create a new entity in the hybrid memory system."""
    try:
        if request.entity_type == EntityType.VOLUNTEER:
            result = await memory_service.create_volunteer_profile(
                volunteer_id=request.entity_id,
                profile_data=request.properties,
                context=context
            )
        elif request.entity_type == EntityType.ORGANIZATION:
            result = await memory_service.create_organization_profile(
                organization_id=request.entity_id,
                profile_data=request.properties,
                context=context
            )
        elif request.entity_type == EntityType.EVENT:
            result = await memory_service.create_event_record(
                event_id=request.entity_id,
                event_data=request.properties,
                context=context
            )
        else:
            # Generic entity creation
            result = await memory_service.memory_system.create_entity(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                properties=request.properties,
                text_content=request.text_content,
                memory_type=request.memory_type,
                context=context
            )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create entity: {str(e)}")


@router.put("/entities/{entity_id}", summary="Update an entity")
async def update_entity(
    entity_id: str,
    request: EntityUpdateRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Update an existing entity in the memory system."""
    try:
        result = await memory_service.update_entity_profile(
            entity_id=entity_id,
            updates=request.properties or {},
            text_content=request.text_content,
            context=context
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update entity: {str(e)}")


@router.delete("/entities/{entity_id}", summary="Delete an entity")
async def delete_entity(
    entity_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
) -> Dict[str, Any]:
    """Delete an entity from the memory system."""
    try:
        result = await memory_service.memory_system.delete_entity(entity_id)
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete entity: {str(e)}")


# Relationship Management Endpoints

@router.post("/relationships/volunteer-event-registration", summary="Register volunteer for event")
async def register_volunteer_for_event(
    request: RelationshipRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Register a volunteer for an event."""
    try:
        result = await memory_service.register_volunteer_for_event(
            volunteer_id=request.source_id,
            event_id=request.target_id,
            registration_data=request.relationship_data,
            context=context
        )
        
        return {"success": True, "relationship": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register volunteer: {str(e)}")


@router.post("/relationships/event-attendance", summary="Record event attendance")
async def record_event_attendance(
    request: RelationshipRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Record volunteer attendance at an event."""
    try:
        result = await memory_service.record_event_attendance(
            volunteer_id=request.source_id,
            event_id=request.target_id,
            attendance_data=request.relationship_data,
            context=context
        )
        
        return {"success": True, "relationship": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attendance: {str(e)}")


@router.post("/relationships/collaboration", summary="Record collaboration")
async def record_collaboration(
    request: RelationshipRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Record collaboration between entities."""
    try:
        result = await memory_service.record_collaboration(
            entity1_id=request.source_id,
            entity2_id=request.target_id,
            collaboration_data=request.relationship_data,
            context=context
        )
        
        return {"success": True, "relationship": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record collaboration: {str(e)}")


# Search and Discovery Endpoints

@router.post("/search/volunteers", summary="Search for volunteers")
async def search_volunteers(
    query_text: Optional[str] = Query(None, description="Text query for volunteer search"),
    skills: Optional[List[str]] = Query(None, description="Required skills"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results to return"),
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Search for volunteers based on criteria."""
    try:
        results = await memory_service.search_volunteers(
            query_text=query_text,
            skills=skills,
            location=location,
            limit=limit,
            context=context
        )
        
        return {
            "success": True,
            "results": [
                {
                    "entity_id": result.entity_id,
                    "content": result.content,
                    "similarity_score": result.similarity_score,
                    "relationships": result.relationships
                }
                for result in results
            ],
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Volunteer search failed: {str(e)}")


@router.post("/search/events", summary="Search for events")
async def search_events(
    query_text: Optional[str] = Query(None, description="Text query for event search"),
    location: Optional[str] = Query(None, description="Location filter"),
    skills_required: Optional[List[str]] = Query(None, description="Skills required"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results to return"),
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Search for events based on criteria."""
    try:
        results = await memory_service.search_events(
            query_text=query_text,
            location=location,
            skills_required=skills_required,
            limit=limit,
            context=context
        )
        
        return {
            "success": True,
            "results": [
                {
                    "entity_id": result.entity_id,
                    "content": result.content,
                    "similarity_score": result.similarity_score,
                    "relationships": result.relationships
                }
                for result in results
            ],
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event search failed: {str(e)}")


@router.get("/search/similar-volunteers/{volunteer_id}", summary="Find similar volunteers")
async def find_similar_volunteers(
    volunteer_id: str,
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Find volunteers similar to the given volunteer."""
    try:
        similar_volunteers = await memory_service.find_similar_volunteers(
            volunteer_id=volunteer_id,
            similarity_threshold=similarity_threshold,
            limit=limit,
            context=context
        )
        
        return {
            "success": True,
            "similar_volunteers": similar_volunteers,
            "total": len(similar_volunteers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar volunteer search failed: {str(e)}")


@router.get("/recommendations/volunteers/{event_id}", summary="Get volunteer recommendations for event")
async def get_volunteer_recommendations(
    event_id: str,
    limit: int = Query(10, ge=1, le=50),
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Get volunteer recommendations for a specific event."""
    try:
        recommendations = await memory_service.get_volunteer_recommendations(
            event_id=event_id,
            limit=limit,
            context=context
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")


# Context and Analytics Endpoints

@router.get("/context/{entity_id}", response_model=EntityContextResponse, summary="Get entity context")
async def get_entity_context(
    entity_id: str,
    context_depth: int = Query(2, ge=1, le=5),
    memory_service: MemoryService = Depends(get_memory_service)
) -> EntityContextResponse:
    """Get comprehensive context for an entity."""
    try:
        context_data = await memory_service.get_entity_context(
            entity_id=entity_id,
            context_depth=context_depth
        )
        
        return EntityContextResponse(**context_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity context: {str(e)}")


@router.get("/community-insights/{entity_id}", summary="Get community insights")
async def get_community_insights(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5),
    memory_service: MemoryService = Depends(get_memory_service)
) -> Dict[str, Any]:
    """Get community insights around an entity."""
    try:
        insights = await memory_service.get_community_insights(
            entity_id=entity_id,
            depth=depth
        )
        
        return {"success": True, "insights": insights}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get community insights: {str(e)}")


@router.get("/analytics", response_model=MemoryAnalyticsResponse, summary="Get memory system analytics")
async def get_memory_analytics(
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryAnalyticsResponse:
    """Get comprehensive analytics about the memory system."""
    try:
        analytics = await memory_service.get_memory_analytics()
        return MemoryAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory analytics: {str(e)}")


# Workflow Integration Endpoints

@router.post("/workflow-execution", summary="Record workflow execution")
async def record_workflow_execution(
    workflow_id: str,
    workflow_data: Dict[str, Any],
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Record workflow execution in memory."""
    try:
        result = await memory_service.record_workflow_execution(
            workflow_id=workflow_id,
            workflow_data=workflow_data,
            context=context
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow execution: {str(e)}")


@router.post("/decision-point", summary="Record decision point")
async def record_decision_point(
    decision_id: str,
    decision_data: Dict[str, Any],
    related_entities: Optional[List[str]] = None,
    memory_service: MemoryService = Depends(get_memory_service),
    context: MemoryContext = Depends(get_memory_context)
) -> Dict[str, Any]:
    """Record a decision point in memory."""
    try:
        result = await memory_service.record_decision_point(
            decision_id=decision_id,
            decision_data=decision_data,
            related_entities=related_entities,
            context=context
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record decision point: {str(e)}")


# Health Check Endpoint

@router.get("/health", summary="Check memory system health")
async def check_memory_health(
    memory_service: MemoryService = Depends(get_memory_service)
) -> Dict[str, Any]:
    """Check the health status of the memory system."""
    try:
        analytics = await memory_service.get_memory_analytics()
        health_status = analytics.get("system_health", {})
        
        return {
            "status": "healthy" if all(health_status.values()) else "degraded",
            "details": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }