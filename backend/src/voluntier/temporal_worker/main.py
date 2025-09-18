"""Temporal worker for executing workflows and activities."""

import asyncio
import logging
from typing import Any, List

from temporalio.client import Client
from temporalio.worker import Worker

from voluntier.config import settings
from voluntier.temporal_workflows import (
    VolunteerManagementWorkflow,
    EventManagementWorkflow,
    NotificationWorkflow,
    SecurityMonitoringWorkflow,
    DataSyncWorkflow,
    AgentOrchestrationWorkflow,
)
from voluntier.temporal_workflows.activities import (
    volunteer_activities,
    event_activities,
    notification_activities,
    security_activities,
    data_activities,
    llm_activities,
)
from voluntier.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def create_temporal_client() -> Client:
    """Create and return a Temporal client."""
    try:
        client = await Client.connect(
            settings.temporal.host,
            namespace=settings.temporal.namespace,
        )
        logger.info(f"Connected to Temporal server at {settings.temporal.host}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {str(e)}")
        raise


async def create_worker(client: Client) -> Worker:
    """Create and configure a Temporal worker."""
    
    # Collect all activity methods
    activities = []
    
    # Volunteer activities
    activities.extend([
        volunteer_activities.validate_user_profile,
        volunteer_activities.check_duplicate_registration,
        volunteer_activities.create_user_profile,
        volunteer_activities.initiate_verification,
        volunteer_activities.find_matching_volunteers,
        volunteer_activities.update_volunteer_stats,
        volunteer_activities.get_volunteer_recommendations,
    ])
    
    # Event activities (placeholder - would be implemented similarly)
    # activities.extend([...])
    
    # Notification activities (placeholder)
    # activities.extend([...])
    
    # Security activities (placeholder)
    # activities.extend([...])
    
    # Data activities (placeholder)
    # activities.extend([...])
    
    # LLM activities
    activities.extend([
        llm_activities.analyze_context_and_decide,
        llm_activities.check_human_approval_required,
        llm_activities.execute_agent_action,
        llm_activities.monitor_and_learn,
        llm_activities.get_approval_status,
        llm_activities.personalize_content,
    ])
    
    # Create worker
    worker = Worker(
        client,
        task_queue=settings.temporal.task_queue,
        workflows=[
            VolunteerManagementWorkflow,
            EventManagementWorkflow,
            NotificationWorkflow,
            SecurityMonitoringWorkflow,
            DataSyncWorkflow,
            AgentOrchestrationWorkflow,
        ],
        activities=activities,
        workflow_runner=None,  # Use default
        activity_executor=None,  # Use default
        max_concurrent_activities=50,
        max_concurrent_workflow_tasks=10,
    )
    
    logger.info(f"Created Temporal worker with {len(activities)} activities and 6 workflows")
    return worker


async def run_worker():
    """Run the Temporal worker."""
    setup_logging()
    
    logger.info("Starting Temporal worker...")
    
    try:
        # Create client and worker
        client = await create_temporal_client()
        worker = await create_worker(client)
        
        logger.info(f"Worker running on task queue: {settings.temporal.task_queue}")
        
        # Run the worker
        await worker.run()
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        raise
    finally:
        logger.info("Worker shutting down")


if __name__ == "__main__":
    asyncio.run(run_worker())