"""Verification workflow for identity verification process.

This workflow orchestrates the multi-step verification process with:
- Multiple verification methods (document, community, in-person, trust network, activity)
- Parallel processing of independent verification steps
- Automatic score calculation and updates
- Retry logic with exponential backoff
- Timeout handling for long-running verifications
- Signal handling for real-time updates

The workflow is designed to be:
- Durable: Survives worker crashes and restarts
- Observable: Progress can be queried at any time
- Flexible: Supports adding new verification methods dynamically
- Fair: No single verification method is required (multiple pathways)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities with passthrough (they're deterministic)
with workflow.unsafe.imports_passed_through():
    from app.activities.verification import (
        VerificationMethod,
        calculate_verification_score,
        check_trust_network_strength,
        record_verification_method,
        send_verification_notification,
        update_user_verification_score,
    )


@dataclass
class VerificationInput:
    """Input for verification workflow.

    Attributes:
        user_id: ID of user to verify.
        initial_methods: Initial verification methods to attempt (optional).
        target_score: Target verification score (default 50, max 100).
        timeout_days: Maximum days to wait for verification completion.
    """

    user_id: int
    initial_methods: list[str] | None = None
    target_score: float = 50.0
    timeout_days: int = 30


@dataclass
class VerificationResult:
    """Result of verification workflow.

    Attributes:
        user_id: ID of verified user.
        final_score: Final verification score achieved.
        methods_completed: List of completed verification methods.
        completed_at: ISO timestamp of completion.
        status: Status (completed, timeout, cancelled).
    """

    user_id: int
    final_score: float
    methods_completed: list[dict[str, Any]]
    completed_at: str
    status: str


@workflow.defn
class VerificationWorkflow:
    """Multi-step identity verification workflow.

    This workflow manages the entire verification process:
    1. Initialize with user ID and target score
    2. Wait for verification method completions (via signals)
    3. Calculate scores in real-time
    4. Update database with progress
    5. Complete when target score reached or timeout

    Signals:
        complete_verification_method: Add a completed verification method
        update_trust_network: Recalculate trust network score
        cancel_verification: Cancel the workflow early

    Queries:
        current_score: Get current verification score
        methods_completed: Get list of completed methods

    Example:
        >>> # Start verification workflow
        >>> handle = await client.start_workflow(
        ...     VerificationWorkflow.run,
        ...     VerificationInput(user_id=123, target_score=60.0),
        ...     id=f"verification-123",
        ...     task_queue="verification-queue",
        ... )
        >>>
        >>> # User completes community validation
        >>> await handle.signal(
        ...     VerificationWorkflow.complete_verification_method,
        ...     "community", 20.0, {"validator_id": 456}
        ... )
        >>>
        >>> # Check progress
        >>> score = await handle.query(VerificationWorkflow.current_score)
        >>> print(f"Current score: {score}")
        >>>
        >>> # Wait for completion
        >>> result = await handle.result()
        >>> print(f"Final score: {result.final_score}")
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self._user_id: int = 0
        self._target_score: float = 50.0
        self._current_score: float = 0.0
        self._methods_completed: list[dict[str, Any]] = []
        self._verification_complete = asyncio.Event()
        self._cancelled = False
        self._timeout_reached = False

    @workflow.run
    async def run(self, input: VerificationInput) -> VerificationResult:
        """Main workflow execution.

        Args:
            input: Verification workflow input.

        Returns:
            VerificationResult: Final verification result.
        """
        self._user_id = input.user_id
        self._target_score = min(input.target_score, 100.0)

        workflow.logger.info(
            f"Starting verification workflow for user {self._user_id}, "
            f"target score: {self._target_score}"
        )

        # Set search attributes for queryability
        workflow.upsert_search_attributes(
            {
                "user_id": [self._user_id],
                "verification_status": ["in_progress"],
                "target_score": [self._target_score],
                "created_at": [datetime.utcnow()],
                "verification_methods_count": [0],
            }
        )

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )

        # Process any initial verification methods
        if input.initial_methods:
            workflow.logger.info(
                f"Processing {len(input.initial_methods)} initial methods"
            )
            for method_type in input.initial_methods:
                # This would trigger specific verification flows
                # For now, we just log them
                workflow.logger.info(f"Initial method: {method_type}")

        # Main verification loop - wait for signals or timeout
        try:
            timeout = timedelta(days=input.timeout_days)
            await workflow.wait_condition(
                lambda: self._verification_complete.is_set() or self._cancelled,
                timeout=timeout,
            )

            status = "completed" if self._verification_complete.is_set() else "timeout"
            if self._cancelled:
                status = "cancelled"

        except asyncio.TimeoutError:
            workflow.logger.warning(
                f"Verification timeout reached after {input.timeout_days} days"
            )
            self._timeout_reached = True
            status = "timeout"

        # Final score calculation with trust network
        if not self._cancelled:
            try:
                # Check trust network for additional points
                trust_score = await workflow.execute_activity(
                    check_trust_network_strength,
                    self._user_id,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                if trust_score > 0:
                    workflow.logger.info(
                        f"Adding trust network score: {trust_score} points"
                    )
                    # Add trust network as a method
                    await self._record_method(
                        "trust_network",
                        trust_score,
                        {"calculated_at": datetime.now().isoformat()},
                    )

            except Exception as e:
                workflow.logger.error(f"Failed to calculate trust score: {e}")

        # Calculate final score
        final_score = await workflow.execute_activity(
            calculate_verification_score,
            self._user_id,
            self._methods_completed,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        self._current_score = final_score

        # Update database with final score
        if not self._cancelled:
            try:
                await workflow.execute_activity(
                    update_user_verification_score,
                    self._user_id,
                    final_score,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                # Send completion notification
                await workflow.execute_activity(
                    send_verification_notification,
                    self._user_id,
                    "verification_complete",
                    {
                        "score": final_score,
                        "status": status,
                        "methods_count": len(self._methods_completed),
                    },
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

            except Exception as e:
                workflow.logger.error(f"Failed to update final score: {e}")

        workflow.logger.info(
            f"Verification workflow completed for user {self._user_id}, "
            f"final score: {final_score}, status: {status}"
        )

        return VerificationResult(
            user_id=self._user_id,
            final_score=final_score,
            methods_completed=self._methods_completed,
            completed_at=workflow.now().isoformat(),
            status=status,
        )

    async def _record_method(
        self, method_type: str, weight: float, evidence: dict[str, Any]
    ) -> None:
        """Record a verification method completion.

        Args:
            method_type: Type of verification method.
            weight: Score weight for this method.
            evidence: Method-specific evidence data.
        """
        method = VerificationMethod(
            method=method_type,
            weight=weight,
            evidence=evidence,
            completed_at=workflow.now().isoformat(),
        )

        # Record in database
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )

        result = await workflow.execute_activity(
            record_verification_method,
            self._user_id,
            method,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Update local state
        self._methods_completed = result["methods"]

        # Recalculate current score
        self._current_score = await workflow.execute_activity(
            calculate_verification_score,
            self._user_id,
            self._methods_completed,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Update database with new score
        await workflow.execute_activity(
            update_user_verification_score,
            self._user_id,
            self._current_score,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Send progress notification
        await workflow.execute_activity(
            send_verification_notification,
            self._user_id,
            "method_completed",
            {
                "method": method_type,
                "weight": weight,
                "current_score": self._current_score,
                "target_score": self._target_score,
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        workflow.logger.info(
            f"Recorded {method_type} method, current score: {self._current_score}/{self._target_score}"
        )

        # Update search attributes with new methods count
        workflow.upsert_search_attributes(
            {"verification_methods_count": [len(self._methods_completed)]}
        )

        # Check if target reached
        if self._current_score >= self._target_score:
            workflow.logger.info("Target score reached, completing verification")
            # Update status to completed
            workflow.upsert_search_attributes({"verification_status": ["completed"]})
            self._verification_complete.set()

    @workflow.signal
    async def complete_verification_method(
        self, method_type: str, weight: float, evidence: dict[str, Any]
    ) -> None:
        """Signal to add a completed verification method.

        This signal is called when a user completes a verification step
        (e.g., uploads a document, gets community validation, etc.).

        Args:
            method_type: Type of verification (document, community, in_person, etc).
            weight: Score weight for this method (0-100).
            evidence: Method-specific evidence data.
        """
        workflow.logger.info(
            f"Received {method_type} verification completion signal, weight: {weight}"
        )
        await self._record_method(method_type, weight, evidence)

    @workflow.signal
    async def update_trust_network(self) -> None:
        """Signal to recalculate trust network score.

        Called when a user's trust network changes (new connections, etc.).
        """
        workflow.logger.info("Recalculating trust network score")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        try:
            trust_score = await workflow.execute_activity(
                check_trust_network_strength,
                self._user_id,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            if trust_score > 0:
                await self._record_method(
                    "trust_network",
                    trust_score,
                    {"recalculated_at": workflow.now().isoformat()},
                )

        except Exception as e:
            workflow.logger.error(f"Failed to update trust network: {e}")

    @workflow.signal
    async def cancel_verification(self) -> None:
        """Signal to cancel the verification process."""
        workflow.logger.info("Received cancellation signal")
        self._cancelled = True
        self._verification_complete.set()

    @workflow.query
    def current_score(self) -> float:
        """Query current verification score.

        Returns:
            float: Current verification score (0-100).
        """
        return self._current_score

    @workflow.query
    def methods_completed(self) -> list[dict[str, Any]]:
        """Query list of completed verification methods.

        Returns:
            list: List of completed method dictionaries.
        """
        return self._methods_completed

    @workflow.query
    def progress_percentage(self) -> float:
        """Query verification progress as percentage.

        Returns:
            float: Progress percentage (0-100).
        """
        if self._target_score == 0:
            return 100.0
        return min((self._current_score / self._target_score) * 100, 100.0)
