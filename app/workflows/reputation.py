"""Reputation workflow with continue-as-new for long-running processes.

This workflow manages reputation decay over time using the continue-as-new pattern
to avoid workflow history limits (50K events). The workflow can run indefinitely
by restarting with new state while maintaining durability.

Based on Temporal Python SDK best practices from Context7.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy


@dataclass
class ReputationDecayInput:
    """Input for reputation decay workflow.

    Attributes:
        user_id: User ID to manage reputation for.
        decay_interval_days: Days between each decay calculation (default: 30).
        max_iterations: Maximum iterations before stopping (default: 1000 = 83 years).
        current_iteration: Current iteration count (used for continue-as-new).
    """

    user_id: int
    decay_interval_days: int = 30
    max_iterations: int = 1000
    current_iteration: int = 0


@dataclass
class ReputationDecayResult:
    """Result from reputation decay workflow.

    Attributes:
        user_id: User ID.
        iterations_completed: Number of decay cycles completed.
        final_reputation: Final reputation score.
        stopped_reason: Why workflow stopped (max_iterations, cancelled, error).
    """

    user_id: int
    iterations_completed: int
    final_reputation: float
    stopped_reason: str


@workflow.defn
class ReputationDecayWorkflow:
    """Long-running reputation decay workflow using continue-as-new.

    This workflow applies time decay to user reputation scores every N days.
    It uses continue-as-new to avoid workflow history limits, allowing it to
    run indefinitely (years+) while maintaining constant memory usage.

    Pattern:
    1. Sleep for decay_interval_days
    2. Execute decay activity
    3. Check if should continue
    4. If yes: continue_as_new with incremented iteration
    5. If no: return final result

    Example:
        >>> # Start reputation decay for user (runs for years)
        >>> handle = await client.start_workflow(
        ...     ReputationDecayWorkflow.run,
        ...     ReputationDecayInput(user_id=123, decay_interval_days=30),
        ...     id=f"reputation-decay-{user_id}",
        ...     task_queue="reputation-queue"
        ... )
        >>>
        >>> # Cancel if needed
        >>> await handle.cancel()
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self._cancelled = False
        self._current_reputation: float = 0.0

    @workflow.run
    async def run(self, input: ReputationDecayInput) -> ReputationDecayResult:
        """Execute reputation decay workflow with continue-as-new.

        Args:
            input: Reputation decay input parameters.

        Returns:
            ReputationDecayResult: Final decay result (only when workflow stops).
        """
        workflow.logger.info(
            f"Starting reputation decay workflow for user {input.user_id}, "
            f"iteration {input.current_iteration}/{input.max_iterations}"
        )

        # Sleep for decay interval
        workflow.logger.info(f"Sleeping for {input.decay_interval_days} days")
        try:
            await workflow.wait_condition(
                lambda: self._cancelled,
                timeout=timedelta(days=input.decay_interval_days),
            )
        except asyncio.TimeoutError:
            # Timeout is expected - time to decay reputation
            pass

        if self._cancelled:
            workflow.logger.info("Workflow cancelled by signal")
            return ReputationDecayResult(
                user_id=input.user_id,
                iterations_completed=input.current_iteration,
                final_reputation=self._current_reputation,
                stopped_reason="cancelled",
            )

        # Execute reputation decay activity
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )

        try:
            # Decay reputation (activity will fetch current score, apply decay, update DB)
            self._current_reputation = await workflow.execute_activity(
                decay_reputation_score,
                input.user_id,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )

            workflow.logger.info(
                f"Reputation decay applied, new score: {self._current_reputation}"
            )

        except Exception as e:
            workflow.logger.error(f"Failed to decay reputation: {e}")
            # Don't fail workflow, just continue (will retry next interval)

        # Check if should continue
        next_iteration = input.current_iteration + 1

        if next_iteration >= input.max_iterations:
            workflow.logger.info(
                f"Reached max iterations ({input.max_iterations}), stopping"
            )
            return ReputationDecayResult(
                user_id=input.user_id,
                iterations_completed=next_iteration,
                final_reputation=self._current_reputation,
                stopped_reason="max_iterations",
            )

        # Continue as new to prevent history bloat
        workflow.logger.info(f"Continuing as new workflow (iteration {next_iteration})")

        workflow.continue_as_new(
            ReputationDecayInput(
                user_id=input.user_id,
                decay_interval_days=input.decay_interval_days,
                max_iterations=input.max_iterations,
                current_iteration=next_iteration,
            )
        )

        # This code is never reached due to continue_as_new
        # but Python requires a return statement
        return ReputationDecayResult(
            user_id=input.user_id,
            iterations_completed=next_iteration,
            final_reputation=self._current_reputation,
            stopped_reason="continue_as_new",
        )

    @workflow.signal
    async def cancel_decay(self) -> None:
        """Signal to cancel reputation decay workflow.

        Stops the workflow at the next decay interval.
        """
        workflow.logger.info("Received cancel signal")
        self._cancelled = True

    @workflow.query
    def current_reputation(self) -> float:
        """Query current reputation score.

        Returns:
            float: Current reputation score after last decay.
        """
        return self._current_reputation

    @workflow.query
    def is_cancelled(self) -> bool:
        """Query if workflow is cancelled.

        Returns:
            bool: True if workflow received cancel signal.
        """
        return self._cancelled


# Activity definition (would be in activities/reputation.py in production)
@activity.defn
async def decay_reputation_score(user_id: int) -> float:
    """Apply time decay to user reputation score.

    Reputation decays over time to incentivize continued positive contributions.
    Decay formula: new_score = old_score * 0.95 (5% decay per interval)

    Args:
        user_id: User ID to decay reputation for.

    Returns:
        float: New reputation score after decay.

    Note:
        This is a placeholder. In production, move to app/activities/reputation.py
    """
    workflow.logger.info(f"Decaying reputation for user {user_id}")

    # Fetch current reputation from database
    from app.database import get_session_factory
    from app.models import User

    async with get_session_factory()() as session:
        user = await session.get(User, user_id)

        if not user:
            workflow.logger.warning(f"User {user_id} not found")
            return 0.0

        old_score = user.reputation_score or 0.0

        # Apply 5% decay
        new_score = max(old_score * 0.95, 0.0)

        # Update database
        user.reputation_score = new_score
        await session.commit()

        workflow.logger.info(
            f"Reputation decayed from {old_score:.2f} to {new_score:.2f}"
        )

        return new_score
