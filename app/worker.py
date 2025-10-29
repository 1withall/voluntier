"""Temporal worker for executing workflows and activities.

This worker connects to the Temporal server and polls for workflow and activity tasks.
It handles verification workflows and all related activities.

Enhanced with interceptors for automatic logging and metrics collection.
"""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.activities.verification import (
    calculate_verification_score,
    check_trust_network_strength,
    record_verification_method,
    send_verification_notification,
    update_user_verification_score,
    # Phase 2: Child workflow support activities
    extract_document_data,
    check_document_validity,
    store_verification_evidence,
    request_community_validators,
    aggregate_validation_scores,
    find_available_verifiers,
    schedule_verification_appointment,
)
from app.activities.local import (
    check_user_exists_local,
    get_user_email_local,
    get_user_reputation_local,
    get_user_verification_score_local,
)
from app.config import settings
from app.core.interceptors import LoggingInterceptor, MetricsInterceptor
from app.workflows.verification import VerificationWorkflow
from app.workflows.reputation import ReputationDecayWorkflow, decay_reputation_score
from app.workflows.verification_subworkflows import (
    DocumentVerificationWorkflow,
    CommunityValidationWorkflow,
    InPersonVerificationWorkflow,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start Temporal worker.

    Connects to Temporal server and starts worker that:
    - Processes VerificationWorkflow instances
    - Executes verification activities
    - Handles signals and queries

    Worker runs until interrupted (Ctrl+C).

    Example:
        >>> # Start worker
        >>> uv run python -m app.worker
        >>> # Worker will log:
        >>> INFO: Connected to Temporal server at localhost:7233
        >>> INFO: Worker started on queue: verification-queue
        >>> INFO: Listening for workflows and activities...
    """
    logger.info("Connecting to Temporal server...")

    # Connect to Temporal
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    logger.info(f"Connected to Temporal server at {settings.temporal_host}")
    logger.info(f"Namespace: {settings.temporal_namespace}")
    logger.info(f"Task queue: {settings.temporal_verification_queue}")

    # Create worker with interceptors for observability
    worker = Worker(
        client,
        task_queue=settings.temporal_verification_queue,
        workflows=[
            # Main workflows
            VerificationWorkflow,
            ReputationDecayWorkflow,
            # Phase 2: Child workflows
            DocumentVerificationWorkflow,
            CommunityValidationWorkflow,
            InPersonVerificationWorkflow,
        ],
        activities=[
            # Regular activities
            calculate_verification_score,
            record_verification_method,
            update_user_verification_score,
            send_verification_notification,
            check_trust_network_strength,
            # Local activities (fast, in-process)
            get_user_reputation_local,
            get_user_verification_score_local,
            check_user_exists_local,
            get_user_email_local,
            # Reputation activities
            decay_reputation_score,
            # Phase 2: Child workflow support activities
            extract_document_data,
            check_document_validity,
            store_verification_evidence,
            request_community_validators,
            aggregate_validation_scores,
            find_available_verifiers,
            schedule_verification_appointment,
        ],
        interceptors=[LoggingInterceptor(), MetricsInterceptor()],
        max_concurrent_activities=100,
        max_concurrent_workflow_tasks=50,
    )

    logger.info("Worker started successfully!")
    logger.info(
        "Registered workflows: VerificationWorkflow, ReputationDecayWorkflow, "
        "DocumentVerificationWorkflow, CommunityValidationWorkflow, InPersonVerificationWorkflow"
    )
    logger.info(
        "Registered activities: calculate_verification_score, record_verification_method, "
        "update_user_verification_score, send_verification_notification, check_trust_network_strength, "
        "get_user_reputation_local, get_user_verification_score_local, check_user_exists_local, "
        "get_user_email_local, decay_reputation_score, extract_document_data, check_document_validity, "
        "store_verification_evidence, request_community_validators, aggregate_validation_scores, "
        "find_available_verifiers, schedule_verification_appointment"
    )
    logger.info("Listening for workflows and activities...")
    logger.info("Press Ctrl+C to stop worker")

    # Run worker
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received, stopping worker...")
        logger.info("Worker stopped gracefully")


if __name__ == "__main__":
    asyncio.run(main())
