"""Temporal interceptors for logging and metrics.

Based on Temporal Python SDK best practices from Context7 documentation.
Provides automatic observability for all workflows and activities.
"""

import logging
import time
from typing import Any

from temporalio import activity, workflow
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
)

logger = logging.getLogger(__name__)


class LoggingInterceptor(Interceptor):
    """Intercept workflow and activity execution for comprehensive logging.

    Automatically logs:
    - Workflow start/completion with duration
    - Activity start/completion with duration
    - Errors with full context (workflow_id, run_id, attempt)
    """

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        """Intercept activity execution."""
        return LoggingActivityInboundInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self, input: WorkflowInterceptorClassInput
    ) -> type[WorkflowInboundInterceptor] | None:
        """Return workflow interceptor class."""
        return LoggingWorkflowInboundInterceptor


class LoggingActivityInboundInterceptor(ActivityInboundInterceptor):
    """Activity interceptor for logging."""

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """Log activity execution."""
        start_time = time.time()
        activity_name = input.fn.__name__

        logger.info(
            f"[Activity Start] {activity_name}",
            extra={
                "activity_id": activity.info().activity_id,
                "workflow_id": activity.info().workflow_id,
                "attempt": activity.info().attempt,
            },
        )

        try:
            result = await super().execute_activity(input)
            duration = time.time() - start_time

            logger.info(
                f"[Activity Complete] {activity_name} in {duration:.2f}s",
                extra={
                    "activity_id": activity.info().activity_id,
                    "duration_ms": duration * 1000,
                    "attempt": activity.info().attempt,
                },
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"[Activity Failed] {activity_name}: {e}",
                extra={
                    "activity_id": activity.info().activity_id,
                    "duration_ms": duration * 1000,
                    "attempt": activity.info().attempt,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


class LoggingWorkflowInboundInterceptor(WorkflowInboundInterceptor):
    """Workflow interceptor for logging."""

    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """Log workflow execution."""
        start_time = workflow.now()
        workflow_name = workflow.info().workflow_type

        workflow.logger.info(
            f"[Workflow Start] {workflow_name}",
            extra={
                "workflow_id": workflow.info().workflow_id,
                "run_id": workflow.info().run_id,
                "attempt": workflow.info().attempt,
            },
        )

        try:
            result = await super().execute_workflow(input)
            duration = (workflow.now() - start_time).total_seconds()

            workflow.logger.info(
                f"[Workflow Complete] {workflow_name} in {duration:.1f}s",
                extra={
                    "workflow_id": workflow.info().workflow_id,
                    "duration_seconds": duration,
                },
            )

            return result

        except Exception as e:
            duration = (workflow.now() - start_time).total_seconds()

            workflow.logger.error(
                f"[Workflow Failed] {workflow_name}: {e}",
                extra={
                    "workflow_id": workflow.info().workflow_id,
                    "duration_seconds": duration,
                    "error": str(e),
                },
            )
            raise


class MetricsInterceptor(Interceptor):
    """Intercept workflow and activity execution for metrics collection.

    In production, integrate with Prometheus, StatsD, or Datadog.
    Currently logs metrics for debugging.
    """

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        """Intercept activity execution for metrics."""
        return MetricsActivityInboundInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self, input: WorkflowInterceptorClassInput
    ) -> type[WorkflowInboundInterceptor] | None:
        """Return workflow interceptor class."""
        return MetricsWorkflowInboundInterceptor


class MetricsActivityInboundInterceptor(ActivityInboundInterceptor):
    """Activity interceptor for metrics collection."""

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """Collect activity metrics."""
        start_time = time.time()
        activity_name = input.fn.__name__

        # TODO: Integrate with Prometheus/StatsD
        # metrics.increment(f"activity.{activity_name}.started")

        try:
            result = await super().execute_activity(input)
            duration = time.time() - start_time

            # TODO: Send to metrics backend
            # metrics.timing(f"activity.{activity_name}.duration", duration * 1000)
            # metrics.increment(f"activity.{activity_name}.success")

            logger.debug(f"Metrics: {activity_name} completed in {duration:.2f}s")
            return result

        except Exception:
            # TODO: Track failures
            # metrics.increment(f"activity.{activity_name}.failure")
            raise


class MetricsWorkflowInboundInterceptor(WorkflowInboundInterceptor):
    """Workflow interceptor for metrics collection."""

    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """Collect workflow metrics."""
        # TODO: Integrate with metrics backend
        # workflow_name = workflow.info().workflow_type
        # metrics.increment(f"workflow.{workflow_name}.started")

        try:
            result = await super().execute_workflow(input)

            # TODO: Track success
            # metrics.increment(f"workflow.{workflow_name}.success")

            return result

        except Exception:
            # TODO: Track failures
            # metrics.increment(f"workflow.{workflow_name}.failure")
            raise
