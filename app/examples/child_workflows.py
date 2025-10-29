"""Example: Using Child Workflows in Verification Process

This module demonstrates how to integrate child workflows into the
VerificationWorkflow to handle different verification methods independently.

Following Phase 2: Child Workflows from TEMPORAL_ADVANCED_FEATURES.md
Context7 Pattern: workflow.execute_child_workflow()
"""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.client import Client

# Safe imports for workflow sandbox
with workflow.unsafe.imports_passed_through():
    from app.workflows.verification_subworkflows import (
        DocumentVerificationInput,
        DocumentVerificationWorkflow,
        CommunityValidationInput,
        CommunityValidationWorkflow,
        InPersonVerificationInput,
        InPersonVerificationWorkflow,
    )


# ==================== Example 1: Document Verification ====================


@workflow.defn
class ExampleDocumentVerificationWorkflow:
    """Example workflow showing document verification child workflow usage."""

    @workflow.run
    async def run(self, user_id: int, document_url: str) -> dict:
        """Execute document verification using child workflow.
        
        This demonstrates independent retry policy for document processing,
        allowing OCR failures to retry without affecting parent workflow.
        """
        workflow.logger.info(
            f"Starting example document verification for user {user_id}"
        )

        # Execute child workflow with independent retry policy
        result = await workflow.execute_child_workflow(
            DocumentVerificationWorkflow.run,
            DocumentVerificationInput(
                user_id=user_id,
                document_type="passport",
                document_url=document_url,
                require_ocr=True,
            ),
            id=f"doc-verify-{user_id}-{workflow.uuid4()}",
            # Child workflow has its own retry policy
            retry_policy=RetryPolicy(
                maximum_attempts=3,  # Retry OCR failures up to 3 times
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
            ),
        )

        workflow.logger.info(
            f"Document verification completed: success={result.success}, "
            f"score={result.validity_score}"
        )

        return {
            "success": result.success,
            "validity_score": result.validity_score,
            "extracted_data": result.extracted_data,
        }


# ==================== Example 2: Community Validation ====================


@workflow.defn
class ExampleCommunityValidationWorkflow:
    """Example workflow showing community validation child workflow usage."""

    @workflow.run
    async def run(self, user_id: int) -> dict:
        """Execute community validation using child workflow.
        
        This demonstrates long-running child workflow with signals for
        receiving validator responses.
        """
        workflow.logger.info(
            f"Starting example community validation for user {user_id}"
        )

        # Start child workflow and get handle for interaction
        handle = await workflow.start_child_workflow(
            CommunityValidationWorkflow.run,
            CommunityValidationInput(
                user_id=user_id,
                required_validators=3,
                validator_pool_size=10,
                timeout_hours=72,
            ),
            id=f"community-verify-{user_id}-{workflow.uuid4()}",
            # No retry for community validation (one-time process)
            retry_policy=RetryPolicy(maximum_attempts=1),
        )

        workflow.logger.info(
            f"Community validation child workflow started: {handle.id}"
        )

        # Query progress after some time
        await asyncio.sleep(5)  # Wait 5 seconds

        progress = await handle.query(
            CommunityValidationWorkflow.validation_progress
        )
        workflow.logger.info(
            f"Validation progress: {progress['approvals']}/{progress['required']} approvals"
        )

        # Wait for result
        result = await handle.result()

        workflow.logger.info(
            f"Community validation completed: success={result.success}, "
            f"confidence={result.confidence_score}"
        )

        return {
            "success": result.success,
            "validators_approved": result.validators_approved,
            "validators_rejected": result.validators_rejected,
            "confidence_score": result.confidence_score,
        }


# ==================== Example 3: In-Person Verification ====================


@workflow.defn
class ExampleInPersonVerificationWorkflow:
    """Example workflow showing in-person verification child workflow usage."""

    @workflow.run
    async def run(self, user_id: int, location: str) -> dict:
        """Execute in-person verification using child workflow.
        
        This demonstrates scheduling workflow with signals for completion.
        """
        workflow.logger.info(
            f"Starting example in-person verification for user {user_id}"
        )

        # Execute child workflow
        result = await workflow.execute_child_workflow(
            InPersonVerificationWorkflow.run,
            InPersonVerificationInput(
                user_id=user_id,
                preferred_location=location,
                preferred_time_slots=[
                    "2025-11-01T10:00:00",
                    "2025-11-01T14:00:00",
                    "2025-11-02T10:00:00",
                ],
                verifier_requirements={
                    "certified": True,
                    "min_verifications": 10,
                },
            ),
            id=f"in-person-verify-{user_id}-{workflow.uuid4()}",
            # No retry for scheduling
            retry_policy=RetryPolicy(maximum_attempts=1),
        )

        workflow.logger.info(
            f"In-person verification completed: success={result.success}, "
            f"scheduled={result.appointment_scheduled}"
        )

        return {
            "success": result.success,
            "appointment_scheduled": result.appointment_scheduled,
            "verifier_id": result.verifier_id,
            "verification_date": result.verification_date,
        }


# ==================== Example 4: Parallel Child Workflows ====================


@workflow.defn
class ExampleParallelVerificationWorkflow:
    """Example showing parallel execution of multiple child workflows."""

    @workflow.run
    async def run(self, user_id: int, document_url: str, location: str) -> dict:
        """Execute multiple verification methods in parallel.
        
        This demonstrates running document and community validation
        simultaneously for faster overall verification.
        """
        workflow.logger.info(
            f"Starting parallel verification for user {user_id}"
        )

        # Start both child workflows in parallel
        doc_task = asyncio.create_task(
            workflow.execute_child_workflow(
                DocumentVerificationWorkflow.run,
                DocumentVerificationInput(
                    user_id=user_id,
                    document_type="passport",
                    document_url=document_url,
                ),
                id=f"doc-verify-{user_id}-{workflow.uuid4()}",
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        )

        community_task = asyncio.create_task(
            workflow.execute_child_workflow(
                CommunityValidationWorkflow.run,
                CommunityValidationInput(
                    user_id=user_id,
                    required_validators=3,
                ),
                id=f"community-verify-{user_id}-{workflow.uuid4()}",
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        )

        # Wait for both to complete
        doc_result, community_result = await asyncio.gather(
            doc_task, community_task
        )

        workflow.logger.info(
            f"Parallel verification completed: "
            f"doc_success={doc_result.success}, "
            f"community_success={community_result.success}"
        )

        # Combine results
        overall_success = doc_result.success and community_result.success

        return {
            "success": overall_success,
            "document_verification": {
                "success": doc_result.success,
                "validity_score": doc_result.validity_score,
            },
            "community_validation": {
                "success": community_result.success,
                "confidence_score": community_result.confidence_score,
            },
        }


# ==================== Example 5: Integration Pattern ====================


async def integration_example():
    """Example of how parent VerificationWorkflow could integrate child workflows.
    
    This pattern would be added to the complete_verification_method signal handler
    in app/workflows/verification.py to automatically trigger appropriate child
    workflows based on verification method type.
    """
    # Pseudo-code showing integration pattern:
    
    # In VerificationWorkflow.complete_verification_method():
    """
    @workflow.signal
    async def complete_verification_method(
        self, method_type: str, weight: float, evidence: dict[str, Any]
    ) -> None:
        workflow.logger.info(f"Starting {method_type} verification")
        
        # Route to appropriate child workflow
        if method_type == "document":
            result = await workflow.execute_child_workflow(
                DocumentVerificationWorkflow.run,
                DocumentVerificationInput(
                    user_id=self._user_id,
                    document_type=evidence.get("document_type", "passport"),
                    document_url=evidence["document_url"],
                ),
                id=f"doc-verify-{self._user_id}-{workflow.uuid4()}",
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            
            if result.success:
                await self._record_method(method_type, weight, result.evidence)
        
        elif method_type == "community":
            result = await workflow.execute_child_workflow(
                CommunityValidationWorkflow.run,
                CommunityValidationInput(
                    user_id=self._user_id,
                    required_validators=evidence.get("required_validators", 3),
                ),
                id=f"community-verify-{self._user_id}-{workflow.uuid4()}",
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            
            if result.success:
                await self._record_method(method_type, weight, result.evidence)
        
        elif method_type == "in_person":
            result = await workflow.execute_child_workflow(
                InPersonVerificationWorkflow.run,
                InPersonVerificationInput(
                    user_id=self._user_id,
                    preferred_location=evidence["location"],
                    preferred_time_slots=evidence["time_slots"],
                    verifier_requirements=evidence.get("requirements", {}),
                ),
                id=f"in-person-verify-{self._user_id}-{workflow.uuid4()}",
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            
            if result.success:
                await self._record_method(method_type, weight, result.evidence)
    """
    pass


# ==================== Client Usage Example ====================


async def client_usage_example():
    """Example of starting verification workflows from client code."""
    
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Example 1: Start document verification
    doc_result = await client.execute_workflow(
        ExampleDocumentVerificationWorkflow.run,
        123,  # user_id
        "s3://bucket/docs/passport.jpg",  # document_url
        id="example-doc-verify-123",
        task_queue="verification-queue",
    )
    print(f"Document verification: {doc_result}")
    
    # Example 2: Start community validation with handle for interaction
    handle = await client.start_workflow(
        ExampleCommunityValidationWorkflow.run,
        123,  # user_id
        id="example-community-verify-123",
        task_queue="verification-queue",
    )
    
    # Query progress
    await asyncio.sleep(10)
    progress = await handle.query(
        CommunityValidationWorkflow.validation_progress
    )
    print(f"Validation progress: {progress}")
    
    # Wait for result
    community_result = await handle.result()
    print(f"Community validation: {community_result}")
    
    # Example 3: Parallel verification
    parallel_result = await client.execute_workflow(
        ExampleParallelVerificationWorkflow.run,
        123,  # user_id
        "s3://bucket/docs/passport.jpg",  # document_url
        "123 Main St, City, State",  # location
        id="example-parallel-verify-123",
        task_queue="verification-queue",
    )
    print(f"Parallel verification: {parallel_result}")


if __name__ == "__main__":
    # Run client examples
    asyncio.run(client_usage_example())
