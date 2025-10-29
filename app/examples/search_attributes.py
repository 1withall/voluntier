"""Examples of querying workflows using search attributes.

Search attributes enable powerful queries across running and completed workflows.
These examples show common patterns for production use.

Requirements:
- Search attributes must be configured in Temporal server (see docker-compose.yaml)
- Workflows must set attributes with workflow.upsert_search_attributes()
- Queries use SQL-like syntax with attribute names

Based on Temporal Python SDK best practices from Context7.
"""

import asyncio
from datetime import datetime, timedelta

from temporalio.client import Client


async def query_verification_workflows() -> None:
    """Query verification workflows using search attributes.

    Examples:
    - Find all in-progress verifications for a specific user
    - Find all completed verifications in the last 7 days
    - Find verifications stuck at low scores
    - Count workflows by status
    """
    # Connect to Temporal
    client = await Client.connect("localhost:7233", namespace="default")

    # Example 1: Find all in-progress verifications for user 123
    print("\n=== Example 1: In-progress verifications for user 123 ===")
    async for workflow in client.list_workflows(
        "WorkflowStatus='Running' AND user_id=123"
    ):
        print(f"Workflow ID: {workflow.id}")
        print(f"  Start Time: {workflow.start_time}")
        print(f"  Execution Time: {workflow.execution_time}")

    # Example 2: Find all completed verifications in last 7 days
    print("\n=== Example 2: Completed verifications (last 7 days) ===")
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    async for workflow in client.list_workflows(
        f"verification_status='completed' AND created_at > '{seven_days_ago.isoformat()}'"
    ):
        print(f"Workflow ID: {workflow.id}")
        print(f"  User ID: {workflow.search_attributes.get('user_id', [None])[0]}")
        print(
            f"  Methods: {workflow.search_attributes.get('verification_methods_count', [0])[0]}"
        )

    # Example 3: Find verifications with target score >= 75
    print("\n=== Example 3: High-security verifications (target >= 75) ===")
    async for workflow in client.list_workflows("target_score >= 75.0"):
        print(f"Workflow ID: {workflow.id}")
        print(
            f"  Target Score: {workflow.search_attributes.get('target_score', [0])[0]}"
        )
        print(
            f"  Status: {workflow.search_attributes.get('verification_status', ['unknown'])[0]}"
        )

    # Example 4: Find stuck verifications (in-progress, 0 methods, >24h old)
    print("\n=== Example 4: Stuck verifications (no methods, >24h) ===")
    yesterday = datetime.utcnow() - timedelta(hours=24)
    async for workflow in client.list_workflows(
        f"WorkflowStatus='Running' AND verification_methods_count=0 AND created_at < '{yesterday.isoformat()}'"
    ):
        print(f"Workflow ID: {workflow.id}")
        print(f"  User ID: {workflow.search_attributes.get('user_id', [None])[0]}")
        print(f"  Start Time: {workflow.start_time}")
        print("  ACTION: May need manual intervention or reminder")

    # Example 5: Count workflows by status
    print("\n=== Example 5: Count workflows by status ===")
    statuses = ["in_progress", "completed", "timeout", "cancelled"]
    for status in statuses:
        count = 0
        async for _ in client.list_workflows(f"verification_status='{status}'"):
            count += 1
        print(f"{status}: {count}")

    # Example 6: Find users with multiple verification attempts
    print("\n=== Example 6: Users with multiple verification attempts ===")
    user_workflows = {}
    async for workflow in client.list_workflows(
        "WorkflowStatus='Running' OR WorkflowStatus='Completed'"
    ):
        user_id = workflow.search_attributes.get("user_id", [None])[0]
        if user_id:
            user_workflows[user_id] = user_workflows.get(user_id, 0) + 1

    for user_id, count in sorted(
        user_workflows.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        if count > 1:
            print(f"User {user_id}: {count} verification workflows")


async def query_reputation_workflows() -> None:
    """Query reputation decay workflows.

    Examples:
    - Find all active reputation decay workflows
    - Check workflow runtime/iterations
    """
    client = await Client.connect("localhost:7233", namespace="default")

    print("\n=== Reputation decay workflows ===")
    async for workflow in client.list_workflows(
        "WorkflowType='ReputationDecayWorkflow' AND WorkflowStatus='Running'"
    ):
        print(f"Workflow ID: {workflow.id}")
        print(f"  Start Time: {workflow.start_time}")
        print(f"  Execution Time: {workflow.execution_time}")

        # Query current reputation score
        handle = client.get_workflow_handle(workflow.id)
        try:
            score = await handle.query("current_reputation")
            print(f"  Current Reputation: {score:.2f}")
        except Exception as e:
            print(f"  Could not query reputation: {e}")


async def monitor_verification_progress() -> None:
    """Real-time monitoring of verification progress.

    Use case: Admin dashboard showing verification metrics.
    """
    client = await Client.connect("localhost:7233", namespace="default")

    print("\n=== Verification Progress Dashboard ===")

    # Metric 1: Total verifications by status
    print("\nStatus breakdown:")
    for status in ["in_progress", "completed", "timeout", "cancelled"]:
        count = 0
        async for _ in client.list_workflows(f"verification_status='{status}'"):
            count += 1
        print(f"  {status}: {count}")

    # Metric 2: Average methods completed
    total_methods = 0
    workflow_count = 0
    async for workflow in client.list_workflows("verification_methods_count > 0"):
        methods = workflow.search_attributes.get("verification_methods_count", [0])[0]
        if isinstance(methods, (int, float)):
            total_methods += int(methods)
            workflow_count += 1

    if workflow_count > 0:
        avg_methods = total_methods / workflow_count
        print(f"\nAverage methods per verification: {avg_methods:.2f}")

    # Metric 3: Completion rate for last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    completed_24h = 0
    total_24h = 0
    async for workflow in client.list_workflows(
        f"created_at > '{yesterday.isoformat()}'"
    ):
        total_24h += 1
        status = workflow.search_attributes.get("verification_status", [""])[0]
        if status == "completed":
            completed_24h += 1

    if total_24h > 0:
        completion_rate = (completed_24h / total_24h) * 100
        print(
            f"\nLast 24h completion rate: {completion_rate:.1f}% ({completed_24h}/{total_24h})"
        )


async def cleanup_old_workflows() -> None:
    """Find workflows that should be cancelled or cleaned up.

    Use case: Maintenance tasks to cancel stuck or abandoned workflows.
    """
    client = await Client.connect("localhost:7233", namespace="default")

    print("\n=== Cleanup: Old abandoned workflows ===")

    # Find workflows running for >30 days with no methods completed
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    count = 0

    async for workflow in client.list_workflows(
        f"WorkflowStatus='Running' AND verification_methods_count=0 AND created_at < '{thirty_days_ago.isoformat()}'"
    ):
        print(f"Workflow ID: {workflow.id}")
        print(f"  User ID: {workflow.search_attributes.get('user_id', [None])[0]}")
        print(f"  Age: {(datetime.utcnow() - workflow.start_time).days} days")
        print("  ACTION: Consider cancelling")

        # Optionally cancel
        # handle = client.get_workflow_handle(workflow.id)
        # await handle.cancel()

        count += 1

    print(f"\nFound {count} workflows to clean up")


if __name__ == "__main__":
    print("Temporal Search Attributes Query Examples\n")
    print("=" * 60)

    # Run examples
    asyncio.run(query_verification_workflows())
    asyncio.run(query_reputation_workflows())
    asyncio.run(monitor_verification_progress())
    asyncio.run(cleanup_old_workflows())

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nFor production use:")
    print("1. Add error handling and retries")
    print("2. Implement caching for expensive queries")
    print("3. Use pagination for large result sets")
    print("4. Add Prometheus metrics collection")
    print("5. Build dashboards with Grafana")
