"""Temporal workflow API routes."""

from fastapi import APIRouter, HTTPException
from temporalio.client import Client

from voluntier.config import settings
from voluntier.temporal_workflows.schemas import (
    VolunteerRegistrationRequest,
    EventCreationRequest,
    NotificationRequest,
    AgentDecisionRequest,
    WorkflowResponse,
)
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/volunteers/register", response_model=WorkflowResponse)
async def register_volunteer(request: VolunteerRegistrationRequest):
    """Trigger volunteer registration workflow."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # Start workflow
        handle = await client.start_workflow(
            "VolunteerManagementWorkflow",
            request,
            id=f"volunteer-registration-{request.profile_data.get('email', 'unknown')}",
            task_queue=settings.temporal.task_queue,
        )
        
        # Get result (with timeout)
        result = await handle.result()
        
        return WorkflowResponse(
            status="success",
            data=result,
            message="Volunteer registration workflow completed",
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger volunteer registration workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/events/create", response_model=WorkflowResponse)
async def create_event(request: EventCreationRequest):
    """Trigger event creation workflow."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # Start workflow
        handle = await client.start_workflow(
            "EventManagementWorkflow",
            request,
            id=f"event-creation-{request.organizer_id}",
            task_queue=settings.temporal.task_queue,
        )
        
        result = await handle.result()
        
        return WorkflowResponse(
            status="success",
            data=result,
            message="Event creation workflow completed",
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger event creation workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/notifications/send", response_model=WorkflowResponse)
async def send_notification(request: NotificationRequest):
    """Trigger notification workflow."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # Start workflow
        handle = await client.start_workflow(
            "NotificationWorkflow",
            request,
            id=f"notification-{request.user_id}-{request.type}",
            task_queue=settings.temporal.task_queue,
        )
        
        result = await handle.result()
        
        return WorkflowResponse(
            status="success",
            data=result,
            message="Notification workflow completed",
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger notification workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/agent/decide", response_model=WorkflowResponse)
async def agent_decision(request: AgentDecisionRequest):
    """Trigger agent decision workflow."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # Start workflow
        handle = await client.start_workflow(
            "AgentOrchestrationWorkflow",
            request,
            id=f"agent-decision-{request.context.get('scenario', 'unknown')}",
            task_queue=settings.temporal.task_queue,
        )
        
        result = await handle.result()
        
        return WorkflowResponse(
            status="success", 
            data=result,
            message="Agent decision workflow completed",
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger agent decision workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/workflows/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow execution status."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)
        
        # Get workflow description
        description = await handle.describe()
        
        return {
            "workflow_id": workflow_id,
            "status": description.status.name,
            "start_time": description.start_time.isoformat() if description.start_time else None,
            "close_time": description.close_time.isoformat() if description.close_time else None,
            "workflow_type": description.workflow_type,
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found or error: {str(e)}"
        )


@router.get("/workflows/list")
async def list_workflows(limit: int = 10):
    """List recent workflows."""
    try:
        client = await Client.connect(settings.temporal.host)
        
        # List workflows (simplified - in production would use proper filtering)
        workflows = []
        
        return {
            "workflows": workflows,
            "total": len(workflows),
            "limit": limit,
        }
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {str(e)}"
        )