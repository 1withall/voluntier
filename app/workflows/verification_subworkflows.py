"""Child workflows for verification processes.

This module contains specialized child workflows that handle different
verification methods independently. Each child workflow has its own
retry policy and execution lifecycle, allowing for better fault isolation
and parallel execution.

Following Phase 2: Child Workflows from TEMPORAL_ADVANCED_FEATURES.md
Context7 Pattern: workflow.execute_child_workflow() with independent RetryPolicy
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

# Safe imports for workflow sandbox
with workflow.unsafe.imports_passed_through():
    from app.activities.verification import (
        check_document_validity,
        extract_document_data,
        store_verification_evidence,
    )


@dataclass
class DocumentVerificationInput:
    """Input for document verification child workflow.
    
    Attributes:
        user_id: User requesting verification
        document_type: Type of document (passport, drivers_license, national_id, etc.)
        document_url: S3/storage URL for uploaded document
        require_ocr: Whether to perform OCR extraction (default: True)
    """
    user_id: int
    document_type: str
    document_url: str
    require_ocr: bool = True


@dataclass
class DocumentVerificationResult:
    """Result from document verification.
    
    Attributes:
        success: Whether verification succeeded
        extracted_data: Data extracted from document (name, DOB, ID number, etc.)
        validity_score: Document validity score (0-100)
        evidence: Additional evidence for audit trail
        error_message: Error details if failed
    """
    success: bool
    extracted_data: dict[str, Any]
    validity_score: float
    evidence: dict[str, Any]
    error_message: str | None = None


@workflow.defn
class DocumentVerificationWorkflow:
    """Child workflow for document-based identity verification.
    
    Handles document upload, OCR processing, and validity checking.
    This workflow runs independently with its own retry policy,
    allowing document processing to retry on transient OCR failures
    without affecting the parent VerificationWorkflow.
    
    Example:
        # From parent VerificationWorkflow
        result = await workflow.execute_child_workflow(
            DocumentVerificationWorkflow.run,
            DocumentVerificationInput(
                user_id=user_id,
                document_type="passport",
                document_url="s3://bucket/docs/user123.jpg",
            ),
            id=f"doc-verify-{user_id}-{workflow.uuid4()}",
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
            ),
        )
    """

    @workflow.run
    async def run(self, input: DocumentVerificationInput) -> DocumentVerificationResult:
        """Execute document verification workflow.
        
        Steps:
        1. Extract data from document (OCR if required)
        2. Validate document authenticity and format
        3. Store evidence for audit trail
        4. Return verification result
        
        Args:
            input: Document verification parameters
            
        Returns:
            DocumentVerificationResult with success status and extracted data
        """
        workflow.logger.info(
            f"Starting document verification for user {input.user_id}, "
            f"type: {input.document_type}"
        )

        try:
            # Step 1: Extract data from document
            # For documents requiring OCR (images), this will be a long-running activity
            # with heartbeating (Phase 2 feature)
            extracted_data = await workflow.execute_activity(
                extract_document_data,
                args=[
                    input.user_id,
                    input.document_type,
                    input.document_url,
                    input.require_ocr,
                ],
                start_to_close_timeout=timedelta(minutes=5),
                # Phase 2: Heartbeat timeout for detecting worker crashes
                # If no heartbeat received for 30s, activity is considered failed
                heartbeat_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

            workflow.logger.info(
                f"Extracted data from {input.document_type}: "
                f"{len(extracted_data)} fields"
            )

            # Step 2: Validate document
            validity_result = await workflow.execute_activity(
                check_document_validity,
                args=[input.document_type, extracted_data],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

            workflow.logger.info(
                f"Document validity check: score={validity_result['score']}, "
                f"valid={validity_result['is_valid']}"
            )

            # Step 3: Store evidence
            evidence = {
                "document_type": input.document_type,
                "document_url": input.document_url,
                "extracted_fields": list(extracted_data.keys()),
                "validity_checks": validity_result.get("checks", {}),
                "timestamp": workflow.now().isoformat(),
            }

            await workflow.execute_activity(
                store_verification_evidence,
                args=[input.user_id, "document", evidence],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Return success result
            return DocumentVerificationResult(
                success=validity_result["is_valid"],
                extracted_data=extracted_data,
                validity_score=validity_result["score"],
                evidence=evidence,
            )

        except Exception as e:
            workflow.logger.error(
                f"Document verification failed for user {input.user_id}: {str(e)}"
            )
            return DocumentVerificationResult(
                success=False,
                extracted_data={},
                validity_score=0.0,
                evidence={"error": str(e), "timestamp": workflow.now().isoformat()},
                error_message=str(e),
            )


@dataclass
class CommunityValidationInput:
    """Input for community validation child workflow.
    
    Attributes:
        user_id: User requesting validation
        required_validators: Number of community validators needed
        validator_pool_size: Maximum validators to request from (prevents spam)
        timeout_hours: Hours to wait for validators before timing out
    """
    user_id: int
    required_validators: int = 3
    validator_pool_size: int = 10
    timeout_hours: int = 72


@dataclass
class CommunityValidationResult:
    """Result from community validation.
    
    Attributes:
        success: Whether enough validators approved
        validators_approved: Number of validators who approved
        validators_rejected: Number who rejected
        validator_ids: List of validator user IDs
        confidence_score: Aggregated confidence (0-100)
        evidence: Validation details
    """
    success: bool
    validators_approved: int
    validators_rejected: int
    validator_ids: list[int]
    confidence_score: float
    evidence: dict[str, Any]


@workflow.defn
class CommunityValidationWorkflow:
    """Child workflow for community-based identity validation.
    
    Requests multiple community members to validate a user's identity
    through existing trust networks. Waits for required number of
    validators with timeout.
    
    Uses signals to receive validator responses and queries to check progress.
    
    Example:
        result = await workflow.execute_child_workflow(
            CommunityValidationWorkflow.run,
            CommunityValidationInput(
                user_id=user_id,
                required_validators=3,
                timeout_hours=72,
            ),
            id=f"community-verify-{user_id}-{workflow.uuid4()}",
            retry_policy=RetryPolicy(maximum_attempts=1),  # No retry for community validation
        )
    """

    def __init__(self) -> None:
        self._approvals: list[dict[str, Any]] = []
        self._rejections: list[dict[str, Any]] = []
        self._required_count = 0
        self._validation_complete = False

    @workflow.run
    async def run(
        self, input: CommunityValidationInput
    ) -> CommunityValidationResult:
        """Execute community validation workflow.
        
        Steps:
        1. Request validators from trust network
        2. Wait for required number of responses (with timeout)
        3. Aggregate validation results
        4. Store evidence and return result
        
        Args:
            input: Community validation parameters
            
        Returns:
            CommunityValidationResult with approval status
        """
        self._required_count = input.required_validators

        workflow.logger.info(
            f"Starting community validation for user {input.user_id}, "
            f"need {input.required_validators} validators"
        )

        # Import activities needed for community validation
        with workflow.unsafe.imports_passed_through():
            from app.activities.verification import (
                request_community_validators,
                aggregate_validation_scores,
            )

        try:
            # Step 1: Request validators from trust network
            validator_ids = await workflow.execute_activity(
                request_community_validators,
                args=[input.user_id, input.validator_pool_size],
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"Requested validation from {len(validator_ids)} community members"
            )

            # Step 2: Wait for validators to respond (with timeout)
            timeout = timedelta(hours=input.timeout_hours)
            
            try:
                await workflow.wait_condition(
                    lambda: len(self._approvals) + len(self._rejections)
                    >= input.required_validators
                    or self._validation_complete,
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                workflow.logger.warning(
                    f"Community validation timed out after {input.timeout_hours}h, "
                    f"got {len(self._approvals)} approvals, {len(self._rejections)} rejections"
                )

            # Step 3: Aggregate results
            total_responses = len(self._approvals) + len(self._rejections)
            success = len(self._approvals) >= input.required_validators

            # Calculate confidence score based on validator reputation
            confidence_score = await workflow.execute_activity(
                aggregate_validation_scores,
                args=[self._approvals, self._rejections],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 4: Store evidence
            evidence = {
                "validator_count": len(validator_ids),
                "approvals": len(self._approvals),
                "rejections": len(self._rejections),
                "total_responses": total_responses,
                "required_validators": input.required_validators,
                "timeout_hours": input.timeout_hours,
                "timed_out": total_responses < input.required_validators,
                "timestamp": workflow.now().isoformat(),
            }

            with workflow.unsafe.imports_passed_through():
                from app.activities.verification import store_verification_evidence

            await workflow.execute_activity(
                store_verification_evidence,
                args=[input.user_id, "community", evidence],
                start_to_close_timeout=timedelta(seconds=10),
            )

            return CommunityValidationResult(
                success=success,
                validators_approved=len(self._approvals),
                validators_rejected=len(self._rejections),
                validator_ids=validator_ids,
                confidence_score=confidence_score,
                evidence=evidence,
            )

        except Exception as e:
            workflow.logger.error(
                f"Community validation failed for user {input.user_id}: {str(e)}"
            )
            return CommunityValidationResult(
                success=False,
                validators_approved=len(self._approvals),
                validators_rejected=len(self._rejections),
                validator_ids=[],
                confidence_score=0.0,
                evidence={"error": str(e), "timestamp": workflow.now().isoformat()},
            )

    @workflow.signal
    async def validator_response(
        self, validator_id: int, approved: bool, comment: str = ""
    ) -> None:
        """Signal handler for validator responses.
        
        Args:
            validator_id: ID of community validator
            approved: Whether validator approved identity
            comment: Optional comment from validator
        """
        response = {
            "validator_id": validator_id,
            "approved": approved,
            "comment": comment,
            "timestamp": workflow.now().isoformat(),
        }

        if approved:
            self._approvals.append(response)
            workflow.logger.info(
                f"Validator {validator_id} APPROVED "
                f"({len(self._approvals)}/{self._required_count})"
            )
        else:
            self._rejections.append(response)
            workflow.logger.info(
                f"Validator {validator_id} REJECTED "
                f"({len(self._rejections)} rejections)"
            )

    @workflow.query
    def validation_progress(self) -> dict[str, Any]:
        """Query current validation progress.
        
        Returns:
            Progress details with approval/rejection counts
        """
        return {
            "approvals": len(self._approvals),
            "rejections": len(self._rejections),
            "required": self._required_count,
            "complete": len(self._approvals) >= self._required_count,
        }


@dataclass
class InPersonVerificationInput:
    """Input for in-person verification child workflow.
    
    Attributes:
        user_id: User requesting verification
        preferred_location: Preferred verification location (address/coords)
        preferred_time_slots: List of preferred appointment times (ISO format)
        verifier_requirements: Requirements for in-person verifier
    """
    user_id: int
    preferred_location: str
    preferred_time_slots: list[str]
    verifier_requirements: dict[str, Any]


@dataclass
class InPersonVerificationResult:
    """Result from in-person verification.
    
    Attributes:
        success: Whether verification completed successfully
        appointment_scheduled: Whether appointment was scheduled
        verifier_id: ID of person who verified
        verification_date: When verification occurred (ISO format)
        location: Where verification occurred
        evidence: Verification evidence
    """
    success: bool
    appointment_scheduled: bool
    verifier_id: int | None
    verification_date: str | None
    location: str
    evidence: dict[str, Any]


@workflow.defn
class InPersonVerificationWorkflow:
    """Child workflow for in-person identity verification.
    
    Coordinates scheduling and completion of in-person verification
    with authorized verifiers. Tracks appointment lifecycle from
    scheduling through completion.
    
    Example:
        result = await workflow.execute_child_workflow(
            InPersonVerificationWorkflow.run,
            InPersonVerificationInput(
                user_id=user_id,
                preferred_location="123 Main St, City, State",
                preferred_time_slots=["2025-11-01T10:00:00", "2025-11-01T14:00:00"],
                verifier_requirements={"certified": True, "min_verifications": 10},
            ),
            id=f"in-person-verify-{user_id}-{workflow.uuid4()}",
            retry_policy=RetryPolicy(maximum_attempts=1),  # No retry for scheduling
        )
    """

    def __init__(self) -> None:
        self._appointment_scheduled = False
        self._verification_completed = False
        self._verifier_id: int | None = None
        self._verification_date: str | None = None

    @workflow.run
    async def run(
        self, input: InPersonVerificationInput
    ) -> InPersonVerificationResult:
        """Execute in-person verification workflow.
        
        Steps:
        1. Find available verifiers matching requirements
        2. Schedule appointment at preferred time/location
        3. Wait for verifier to complete verification (signal)
        4. Store evidence and return result
        
        Args:
            input: In-person verification parameters
            
        Returns:
            InPersonVerificationResult with completion status
        """
        workflow.logger.info(
            f"Starting in-person verification for user {input.user_id}, "
            f"location: {input.preferred_location}"
        )

        # Import activities
        with workflow.unsafe.imports_passed_through():
            from app.activities.verification import (
                find_available_verifiers,
                schedule_verification_appointment,
                store_verification_evidence,
            )

        try:
            # Step 1: Find available verifiers
            available_verifiers = await workflow.execute_activity(
                find_available_verifiers,
                args=[
                    input.preferred_location,
                    input.preferred_time_slots,
                    input.verifier_requirements,
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )

            if not available_verifiers:
                workflow.logger.warning(
                    f"No available verifiers found for location: {input.preferred_location}"
                )
                return InPersonVerificationResult(
                    success=False,
                    appointment_scheduled=False,
                    verifier_id=None,
                    verification_date=None,
                    location=input.preferred_location,
                    evidence={
                        "error": "No available verifiers",
                        "timestamp": workflow.now().isoformat(),
                    },
                )

            workflow.logger.info(
                f"Found {len(available_verifiers)} available verifiers"
            )

            # Step 2: Schedule appointment
            appointment = await workflow.execute_activity(
                schedule_verification_appointment,
                args=[input.user_id, available_verifiers[0], input.preferred_time_slots[0]],
                start_to_close_timeout=timedelta(seconds=30),
            )

            self._appointment_scheduled = True
            workflow.logger.info(
                f"Scheduled appointment with verifier {appointment['verifier_id']} "
                f"at {appointment['scheduled_time']}"
            )

            # Step 3: Wait for verification completion (7 day timeout)
            try:
                await workflow.wait_condition(
                    lambda: self._verification_completed,
                    timeout=timedelta(days=7),
                )
            except asyncio.TimeoutError:
                workflow.logger.warning(
                    "In-person verification appointment timed out after 7 days"
                )
                return InPersonVerificationResult(
                    success=False,
                    appointment_scheduled=True,
                    verifier_id=appointment["verifier_id"],
                    verification_date=None,
                    location=input.preferred_location,
                    evidence={
                        "error": "Appointment timeout",
                        "scheduled_time": appointment["scheduled_time"],
                        "timestamp": workflow.now().isoformat(),
                    },
                )

            # Step 4: Store evidence
            evidence = {
                "verifier_id": self._verifier_id,
                "verification_date": self._verification_date,
                "location": input.preferred_location,
                "scheduled_time": appointment["scheduled_time"],
                "timestamp": workflow.now().isoformat(),
            }

            await workflow.execute_activity(
                store_verification_evidence,
                args=[input.user_id, "in_person", evidence],
                start_to_close_timeout=timedelta(seconds=10),
            )

            return InPersonVerificationResult(
                success=True,
                appointment_scheduled=True,
                verifier_id=self._verifier_id,
                verification_date=self._verification_date,
                location=input.preferred_location,
                evidence=evidence,
            )

        except Exception as e:
            workflow.logger.error(
                f"In-person verification failed for user {input.user_id}: {str(e)}"
            )
            return InPersonVerificationResult(
                success=False,
                appointment_scheduled=self._appointment_scheduled,
                verifier_id=self._verifier_id,
                verification_date=self._verification_date,
                location=input.preferred_location,
                evidence={"error": str(e), "timestamp": workflow.now().isoformat()},
            )

    @workflow.signal
    async def verification_completed(
        self, verifier_id: int, verification_date: str
    ) -> None:
        """Signal that in-person verification was completed.
        
        Called by verifier after completing identity verification.
        
        Args:
            verifier_id: ID of verifier who completed verification
            verification_date: When verification occurred (ISO format)
        """
        self._verification_completed = True
        self._verifier_id = verifier_id
        self._verification_date = verification_date

        workflow.logger.info(
            f"In-person verification completed by verifier {verifier_id} "
            f"on {verification_date}"
        )

    @workflow.query
    def appointment_status(self) -> dict[str, Any]:
        """Query appointment status.
        
        Returns:
            Status details including scheduling and completion
        """
        return {
            "scheduled": self._appointment_scheduled,
            "completed": self._verification_completed,
            "verifier_id": self._verifier_id,
            "verification_date": self._verification_date,
        }
