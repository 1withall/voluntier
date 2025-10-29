"""Example: Activity Heartbeating for Long-Running Operations

This module demonstrates Phase 2 heartbeating feature for tracking
progress and detecting failures in long-running activities.

Following Phase 2: Heartbeating from TEMPORAL_ADVANCED_FEATURES.md
Context7 Pattern: activity.heartbeat() with progress details
"""

import asyncio
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import CancelledError


# ==================== Example 1: Basic Heartbeating ====================


@activity.defn
async def long_running_activity_with_heartbeat(total_items: int) -> dict:
    """Activity demonstrating basic heartbeating pattern.
    
    Sends heartbeats during long-running processing to:
    - Detect worker crashes (heartbeat timeout)
    - Allow resumption from last heartbeat on retry
    - Provide real-time progress to workflows
    
    Args:
        total_items: Number of items to process
        
    Returns:
        Processing results with item count
    """
    activity.logger.info(f"Starting processing of {total_items} items")
    
    # Check if retrying and have heartbeat details from previous attempt
    heartbeat_details = activity.info().heartbeat_details
    start_item = 0
    
    if heartbeat_details:
        start_item = heartbeat_details[0]
        activity.logger.info(
            f"Resuming from item {start_item + 1}/{total_items} after retry"
        )
    
    processed = []
    
    for i in range(start_item, total_items):
        # Send heartbeat with current progress
        progress = {
            "item": i + 1,
            "total": total_items,
            "progress_pct": ((i + 1) / total_items) * 100,
        }
        
        # Heartbeat with item number (for resumption) and progress details
        activity.heartbeat(i, progress)
        
        activity.logger.info(
            f"Processing item {i + 1}/{total_items} "
            f"({progress['progress_pct']:.1f}%)"
        )
        
        # Simulate item processing
        await asyncio.sleep(0.5)
        
        # Check for cancellation
        if activity.is_cancelled():
            activity.logger.warning(f"Activity cancelled at item {i + 1}")
            raise CancelledError("Processing cancelled by user")
        
        processed.append(f"item-{i}")
    
    return {
        "processed_count": len(processed),
        "items": processed,
    }


@workflow.defn
class ExampleHeartbeatWorkflow:
    """Workflow showing heartbeat configuration."""
    
    @workflow.run
    async def run(self, total_items: int) -> dict:
        """Execute activity with heartbeat monitoring.
        
        The heartbeat_timeout ensures we detect if the worker crashes
        and hasn't sent a heartbeat within the specified interval.
        """
        workflow.logger.info(f"Starting heartbeat workflow with {total_items} items")
        
        result = await workflow.execute_activity(
            long_running_activity_with_heartbeat,
            total_items,
            start_to_close_timeout=timedelta(minutes=5),
            # Phase 2: Heartbeat timeout for detecting failures
            # If no heartbeat received for 10s, activity is failed and retried
            heartbeat_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )
        
        workflow.logger.info(f"Processing completed: {result['processed_count']} items")
        return result


# ==================== Example 2: Document OCR with Heartbeating ====================


@activity.defn
async def ocr_document_pages(
    document_url: str, total_pages: int
) -> dict:
    """Simulate OCR processing with heartbeats per page.
    
    This demonstrates real-world OCR use case where each page
    takes significant time and we want to track progress.
    
    Args:
        document_url: Document to process
        total_pages: Number of pages in document
        
    Returns:
        OCR results with extracted text per page
    """
    activity.logger.info(
        f"Starting OCR on document {document_url} ({total_pages} pages)"
    )
    
    # Check for resume after retry
    heartbeat_details = activity.info().heartbeat_details
    start_page = 0
    extracted_pages = []
    
    if heartbeat_details:
        start_page = heartbeat_details[0]
        extracted_pages = heartbeat_details[1]  # Previous progress
        activity.logger.info(
            f"Resuming OCR from page {start_page + 1}/{total_pages}"
        )
    
    for page in range(start_page, total_pages):
        # Heartbeat with page number and accumulated results
        progress = {
            "page": page + 1,
            "total_pages": total_pages,
            "progress_pct": ((page + 1) / total_pages) * 100,
            "pages_completed": len(extracted_pages),
        }
        
        # Save both page number (for resumption) and extracted data
        activity.heartbeat(page, extracted_pages, progress)
        
        activity.logger.info(
            f"Processing page {page + 1}/{total_pages} "
            f"({progress['progress_pct']:.1f}% complete)"
        )
        
        # Simulate OCR processing time (2-3 seconds per page)
        await asyncio.sleep(2.5)
        
        # Check cancellation
        if activity.is_cancelled():
            activity.logger.warning(f"OCR cancelled at page {page + 1}")
            raise CancelledError("OCR processing cancelled")
        
        # Extract text from page
        extracted_pages.append({
            "page": page + 1,
            "text": f"Mock OCR text from page {page + 1}",
            "confidence": 0.95,
        })
    
    return {
        "document_url": document_url,
        "total_pages": total_pages,
        "pages": extracted_pages,
    }


@workflow.defn
class DocumentOCRWorkflow:
    """Workflow for OCR processing with heartbeating."""
    
    @workflow.run
    async def run(self, document_url: str, total_pages: int) -> dict:
        """Execute OCR with heartbeat monitoring."""
        workflow.logger.info(f"Starting OCR workflow for {document_url}")
        
        result = await workflow.execute_activity(
            ocr_document_pages,
            args=[document_url, total_pages],
            start_to_close_timeout=timedelta(minutes=10),
            # Heartbeat every page (expected every 2-3 seconds)
            # Fail if no heartbeat for 30 seconds
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
            ),
        )
        
        workflow.logger.info(
            f"OCR completed: {result['total_pages']} pages processed"
        )
        return result


# ==================== Example 3: Batch Processing with Heartbeating ====================


@activity.defn
async def process_user_batch(
    user_ids: list[int], batch_size: int = 100
) -> dict:
    """Process large batch of users with progress tracking.
    
    Uses heartbeating to track progress through large batches
    and allow resumption if worker crashes mid-batch.
    
    Args:
        user_ids: List of user IDs to process
        batch_size: Number of users to process per batch
        
    Returns:
        Processing results
    """
    activity.logger.info(f"Processing {len(user_ids)} users")
    
    # Resume from last heartbeat
    heartbeat_details = activity.info().heartbeat_details
    start_idx = 0
    processed = []
    
    if heartbeat_details:
        start_idx = heartbeat_details[0]
        processed = heartbeat_details[1]
        activity.logger.info(
            f"Resuming from user {start_idx}/{len(user_ids)}"
        )
    
    # Process in batches
    for i in range(start_idx, len(user_ids)):
        # Heartbeat every batch_size users
        if i % batch_size == 0 or i == start_idx:
            progress = {
                "processed": i,
                "total": len(user_ids),
                "progress_pct": (i / len(user_ids)) * 100,
                "batch": i // batch_size + 1,
            }
            activity.heartbeat(i, processed, progress)
            
            activity.logger.info(
                f"Batch {progress['batch']}: {i}/{len(user_ids)} users "
                f"({progress['progress_pct']:.1f}%)"
            )
        
        # Simulate user processing
        await asyncio.sleep(0.01)  # 10ms per user
        
        # Check cancellation periodically
        if i % 10 == 0 and activity.is_cancelled():
            activity.logger.warning(f"Processing cancelled at user {i}")
            raise CancelledError("Batch processing cancelled")
        
        processed.append(user_ids[i])
    
    return {
        "total_users": len(user_ids),
        "processed": len(processed),
        "batches": (len(user_ids) // batch_size) + 1,
    }


@workflow.defn
class BatchProcessingWorkflow:
    """Workflow for batch processing with heartbeating."""
    
    @workflow.run
    async def run(self, user_ids: list[int]) -> dict:
        """Execute batch processing with heartbeat monitoring."""
        workflow.logger.info(f"Starting batch processing for {len(user_ids)} users")
        
        result = await workflow.execute_activity(
            process_user_batch,
            user_ids,
            start_to_close_timeout=timedelta(hours=1),
            # Heartbeat expected every ~1 second (100 users * 10ms)
            # Fail if no heartbeat for 60 seconds
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
            ),
        )
        
        workflow.logger.info(
            f"Batch processing completed: {result['processed']} users"
        )
        return result


# ==================== Client Usage Examples ====================


async def example_heartbeat_usage():
    """Example of running workflows with heartbeating."""
    
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Example 1: Basic heartbeating
    print("\n=== Example 1: Basic Heartbeating ===")
    result1 = await client.execute_workflow(
        ExampleHeartbeatWorkflow.run,
        10,  # total_items
        id="heartbeat-example-1",
        task_queue="verification-queue",
    )
    print(f"Processed: {result1['processed_count']} items")
    
    # Example 2: Document OCR
    print("\n=== Example 2: Document OCR with Heartbeating ===")
    result2 = await client.execute_workflow(
        DocumentOCRWorkflow.run,
        "s3://bucket/docs/passport.pdf",  # document_url
        5,  # total_pages
        id="ocr-example-1",
        task_queue="verification-queue",
    )
    print(f"OCR completed: {result2['total_pages']} pages")
    
    # Example 3: Batch processing
    print("\n=== Example 3: Batch Processing with Heartbeating ===")
    user_ids = list(range(1, 1001))  # 1000 users
    result3 = await client.execute_workflow(
        BatchProcessingWorkflow.run,
        user_ids,
        id="batch-example-1",
        task_queue="verification-queue",
    )
    print(f"Batch processed: {result3['processed']} users in {result3['batches']} batches")


# ==================== Testing Heartbeat Resumption ====================


async def test_heartbeat_resumption():
    """Test that heartbeating allows resumption after failure.
    
    This demonstrates how heartbeat details are persisted and
    activities can resume from last heartbeat after retry.
    """
    print("\n=== Testing Heartbeat Resumption ===")
    
    # Simulate activity that fails mid-processing
    @activity.defn
    async def failing_activity_with_heartbeat(total: int) -> dict:
        """Activity that fails after processing half the items."""
        heartbeat_details = activity.info().heartbeat_details
        start = 0
        
        if heartbeat_details:
            start = heartbeat_details[0]
            print(f"✅ Resumed from item {start} after retry")
        
        for i in range(start, total):
            activity.heartbeat(i, {"processed": i})
            await asyncio.sleep(0.1)
            
            # Simulate failure at halfway point (only on first attempt)
            if i == total // 2 and not heartbeat_details:
                raise Exception("Simulated failure at halfway point")
        
        return {"processed": total}
    
    @workflow.defn
    class ResumptionTestWorkflow:
        @workflow.run
        async def run(self, total: int) -> dict:
            return await workflow.execute_activity(
                failing_activity_with_heartbeat,
                total,
                start_to_close_timeout=timedelta(seconds=30),
                heartbeat_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
    
    # Note: This test would need actual Temporal server to demonstrate resumption
    print("Test workflow defined. Run with Temporal server to see resumption in action.")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_heartbeat_usage())
    
    # Show resumption test
    asyncio.run(test_heartbeat_resumption())
