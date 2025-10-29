# Temporal Advanced Features Integration

**Status**: Phase 2 In Progress (Task 6)  
**Created**: 2025-10-29  
**Updated**: 2025-10-29 22:00 UTC  
**Context7 Source**: `/temporalio/sdk-python` (20,000 tokens documentation reviewed)

This document outlines the integration of Temporal's most advanced features system-wide across the Voluntier platform.

## Overview

Temporal provides 15+ advanced features beyond basic workflows and activities. This integration brings production-grade durability, observability, and scalability to our volunteer platform.

## Feature Categories

### 1. **Workflow Patterns** (Priority: HIGH)
- ✅ **Signals**: Already implemented in `VerificationWorkflow` (3 signals)
- ✅ **Queries**: Already implemented in `VerificationWorkflow` (3 queries)
- ✅ **Continue-as-new**: Implemented in `ReputationDecayWorkflow` for long-running processes
- ⏸️ **Child Workflows**: Sub-workflows for complex verification paths
- ⏸️ **Workflow Updates**: Dynamic modification of running workflows

### 2. **Activity Enhancements** (Priority: HIGH)
- ✅ **Retry Policies**: Already configured in `VerificationWorkflow`
- ✅ **Local Activities**: Implemented 4 fast database lookups in `app/activities/local.py`
- ⏸️ **Heartbeating**: Progress tracking for long activities
- ⏸️ **Activity Timeouts**: Granular timeout controls (start_to_close, schedule_to_start, etc.)
- ⏸️ **Async Completion**: Manual activity completion for external systems

### 3. **Observability** (Priority: MEDIUM)
- ✅ **Interceptors**: Implemented LoggingInterceptor and MetricsInterceptor in `app/core/interceptors.py`
- ✅ **Search Attributes**: Configured 5 attributes, integrated into VerificationWorkflow
- ⏸️ **OpenTelemetry**: Distributed tracing
- ⏸️ **Workflow Replay**: Non-determinism detection

### 4. **Scheduling** (Priority: MEDIUM)
- ⏸️ **Cron Schedules**: Periodic reputation updates
- ⏸️ **Workflow Schedules**: Automated verification reminders
- ⏸️ **Backfills**: Historical schedule execution

### 5. **Data Handling** (Priority: LOW)
- ⏸️ **Custom Data Converters**: Pydantic model serialization
- ⏸️ **Payload Codecs**: Encryption for sensitive data
- ⏸️ **Failure Converters**: Custom error formatting

### 6. **Advanced Patterns** (Priority: LOW)
- ⏸️ **Saga Pattern**: Distributed transaction compensation
- ⏸️ **Side Effects**: Non-deterministic operations (UUIDs, API calls)
- ⏸️ **Versioning**: Multiple workflow versions in production
- ⏸️ **Testing**: Time-skipping test environment (already partially used)

---

## Implementation Status

### Phase 1: Core Enhancements (Week 1) - **✅ COMPLETED**

#### 1.1 Interceptors (`app/core/interceptors.py`) - ✅ DONE
**Purpose**: Centralized logging, metrics, and authentication  
**Status**: ✅ Completed

**Features**:
- `LoggingInterceptor`: Automatic workflow/activity logging with duration tracking
- `MetricsInterceptor`: Prometheus/StatsD integration hooks
- Structured logging with workflow_id, run_id, attempt context

**Usage**:
```python
from app.core.interceptors import LoggingInterceptor, MetricsInterceptor

worker = Worker(
    client,
    task_queue="voluntier-queue",
    workflows=[VerificationWorkflow],
    activities=[...],
    interceptors=[LoggingInterceptor(), MetricsInterceptor()]
)
```

**Benefits**:
- Automatic observability without modifying workflow code
- Consistent logging format across all workflows
- Performance metrics collection (P99 latencies, failure rates)

---

### Phase 2: Production Hardening (Week 2) - **🚧 IN PROGRESS**

#### 2.1 Local Activities (`app/activities/local.py`) - ✅ DONE
**Purpose**: Fast in-process activities for simple database reads  
**Status**: ✅ Completed

**Implemented Functions**:
- `get_user_reputation_local(user_id: int) -> float`
- `get_user_verification_score_local(user_id: int) -> float`
- `check_user_exists_local(user_id: int) -> bool`
- `get_user_email_local(user_id: int) -> str | None`

**Benefits**:
- No task queue overhead (execute in worker process)
- <1 second execution time
- Reduced latency for frequently accessed data

**Usage**:
```python
# In workflow
score = await workflow.execute_local_activity(
    get_user_reputation_local,
    user_id,
    schedule_to_close_timeout=timedelta(seconds=1)
)
```

#### 2.2 Continue-as-new (`app/workflows/reputation.py`) - ✅ DONE
**Purpose**: Long-running reputation decay workflows  
**Status**: ✅ Completed

**Features**:
- `ReputationDecayWorkflow`: 30-day decay intervals
- `decay_reputation_score` activity: 5% time decay per interval
- Prevents workflow history bloat (50K event limit)
- Can run for years+ while maintaining constant memory

**Benefits**:
- Unlimited workflow duration (83+ years with 1000 iterations)
- Constant memory usage regardless of runtime
- Durable state across continues

**Usage**:
```python
# Start reputation decay (runs indefinitely)
handle = await client.start_workflow(
    ReputationDecayWorkflow.run,
    ReputationDecayInput(user_id=123, decay_interval_days=30),
    id=f"reputation-decay-{user_id}",
    task_queue="reputation-queue"
)

# Cancel if needed
await handle.signal(ReputationDecayWorkflow.cancel_decay)
```

#### 2.3 Search Attributes (docker-compose.yaml, VerificationWorkflow) - ✅ DONE
**Purpose**: Query workflows by metadata  
**Status**: ✅ Completed

**Configured Attributes**:
- `user_id` (Int): Filter workflows by user
- `verification_status` (Keyword): in_progress, completed, timeout, cancelled
- `target_score` (Double): Target verification score
- `created_at` (Datetime): Workflow start time
- `verification_methods_count` (Int): Number of methods completed

**Benefits**:
- Query workflows without knowing workflow IDs
- Build admin dashboards and monitoring tools
- Find stuck or abandoned workflows
- Compliance and audit queries

**Usage**:
```python
# Set attributes in workflow
workflow.upsert_search_attributes({
    "user_id": [self._user_id],
    "verification_status": ["in_progress"],
    "target_score": [self._target_score],
})

# Query workflows
async for wf in client.list_workflows("user_id=123 AND verification_status='in_progress'"):
    print(f"Found workflow: {wf.id}")
```

**Examples**: See `app/examples/search_attributes.py` for 6 query patterns

#### 2.4 Child Workflows (`app/workflows/verification_subworkflows.py`) - ✅ DONE
**Purpose**: Decompose complex verification into manageable sub-workflows  
**Status**: ✅ Completed

**Implemented Child Workflows**:
1. `DocumentVerificationWorkflow`: Document upload + OCR processing with heartbeating
   - Handles passport, drivers_license, national_id documents
   - OCR extraction with progress tracking
   - Document validity checking
   - Evidence storage for audit trail

2. `CommunityValidationWorkflow`: Multi-step community vouching with signals
   - Requests validators from trust network
   - Receives validator responses via signals
   - Aggregates validation scores by reputation
   - 72-hour timeout with progress queries

3. `InPersonVerificationWorkflow`: Scheduling + completion tracking
   - Finds available verifiers by location
   - Schedules appointments
   - Tracks completion via signals
   - 7-day appointment timeout

**New Activities** (7 total in `app/activities/verification.py`):
- `extract_document_data`: OCR processing with heartbeating
- `check_document_validity`: Document authenticity validation
- `store_verification_evidence`: Audit trail storage
- `request_community_validators`: Trust network querying
- `aggregate_validation_scores`: Reputation-weighted scoring
- `find_available_verifiers`: Geospatial verifier search
- `schedule_verification_appointment`: Appointment creation

**Benefits**:
- Independent retry policies per verification method (3 attempts for document, 1 for community)
- Parallel execution of verification paths (document + community simultaneously)
- Better workflow history manageability (each child has own history)
- Fault isolation (document OCR failure doesn't affect community validation)

**Usage**:
```python
# Execute document verification child workflow
result = await workflow.execute_child_workflow(
    DocumentVerificationWorkflow.run,
    DocumentVerificationInput(
        user_id=user_id,
        document_type="passport",
        document_url="s3://bucket/docs/passport.jpg",
    ),
    id=f"doc-verify-{user_id}-{workflow.uuid4()}",
    retry_policy=RetryPolicy(maximum_attempts=3),
)

# Parallel execution of multiple child workflows
doc_task = asyncio.create_task(
    workflow.execute_child_workflow(DocumentVerificationWorkflow.run, ...)
)
community_task = asyncio.create_task(
    workflow.execute_child_workflow(CommunityValidationWorkflow.run, ...)
)
doc_result, community_result = await asyncio.gather(doc_task, community_task)
```

**Examples**: See `app/examples/child_workflows.py` for:
- Individual child workflow execution
- Parallel child workflow execution
- Integration with parent VerificationWorkflow

#### 2.5 Heartbeating (`app/activities/verification.py`, workflows) - ✅ DONE
**Purpose**: Track progress and detect failures in long-running activities  
**Status**: ✅ Completed

**Implementation**:
- Enhanced `extract_document_data` activity with page-by-page heartbeating
- Processes multi-page documents with progress tracking
- Resumes from last heartbeat after worker crash/retry
- Detects cancellation with `activity.is_cancelled()`

**Features**:
- **Progress Tracking**: Reports page number, progress percentage, pages completed
- **Resumption**: Uses `activity.info().heartbeat_details` to resume from last page
- **Failure Detection**: `heartbeat_timeout=30s` in workflow detects worker crashes
- **Cancellation Support**: Cleanly handles user cancellation mid-processing

**Benefits**:
- Real-time progress monitoring for long OCR operations
- Automatic resumption after transient failures
- Early detection of worker crashes (no need to wait for full timeout)
- User-friendly cancellation without data loss

**Usage in Activity**:
```python
@activity.defn
async def extract_document_data(user_id, document_type, document_url, require_ocr):
    # Check for resume after retry
    heartbeat_details = activity.info().heartbeat_details
    start_page = heartbeat_details[0] if heartbeat_details else 0
    
    for page in range(start_page, total_pages):
        # Send heartbeat with progress
        progress = {
            "page": page + 1,
            "total_pages": total_pages,
            "progress_pct": ((page + 1) / total_pages) * 100,
        }
        activity.heartbeat(page, progress)
        
        # Process page...
        await process_page(page)
        
        # Check cancellation
        if activity.is_cancelled():
            raise CancelledError("OCR cancelled by user")
```

**Usage in Workflow**:
```python
result = await workflow.execute_activity(
    extract_document_data,
    args=[user_id, document_type, document_url, True],
    start_to_close_timeout=timedelta(minutes=5),
    heartbeat_timeout=timedelta(seconds=30),  # Fail if no heartbeat for 30s
    retry_policy=RetryPolicy(maximum_attempts=3),
)
```

**Examples**: See `app/examples/heartbeating.py` for:
- Basic heartbeating pattern
- Document OCR with page-level progress
- Batch processing with heartbeats
- Resumption after failure demo

#### 2.6 Cron Schedules - ⏸️ PLANNED
**Purpose**: Automated periodic workflow execution  
**Status**: ⏸️ Planned for Phase 2 completion

**Planned Schedules**:
1. Daily reputation decay (2 AM UTC)
2. Weekly verification reminders
3. Monthly verification report generation

#### 2.7 Pydantic Data Converter - ⏸️ PLANNED
**Purpose**: Type-safe workflow input/output serialization  
**Status**: ⏸️ Planned for Phase 2 completion

**Planned Changes**:
- Convert workflow input/output classes to Pydantic BaseModel
- Configure `pydantic_data_converter` in worker
- Automatic validation of workflow parameters

#### 1.3 Continue-as-new (`app/workflows/reputation.py`)
**Purpose**: Long-running reputation decay without workflow history limits  
**Status**: ⏸️ Planned

**Use Case**: Reputation scores decay over time (months/years), requiring continuous recalculation.

**Pattern**:
```python
@workflow.defn
class ReputationDecayWorkflow:
    @workflow.run
    async def run(self, user_id: int, iteration: int = 0) -> None:
        # Decay reputation every 30 days
        await workflow.sleep(timedelta(days=30))
        
        # Recalculate reputation
        await workflow.execute_activity(
            decay_reputation_score,
            user_id,
            start_to_close_timeout=timedelta(seconds=60)
        )
        
        # Continue as new to prevent history bloat
        if iteration < 1000:  # Max 83 years
            await workflow.continue_as_new(user_id, iteration + 1)
```

**Benefits**:
- Unlimited workflow duration (years+)
- Constant memory/history size
- No workflow history limits (50K events limit avoided)

#### 1.4 Local Activities (`app/activities/local.py`)
**Purpose**: Fast, in-process activities for simple database reads  
**Status**: ⏸️ Planned

**Use Cases**:
- User reputation lookup (single query)
- Verification score read (no writes)
- Trust network strength (cached data)

**Characteristics**:
- Execute in worker process (no task queue)
- < 1 second execution time
- No retries (fail fast)
- Lower latency (no network overhead)

**Example**:
```python
@activity.defn
async def get_user_reputation_local(user_id: int) -> float:
    """Local activity for fast reputation lookup."""
    async with get_session() as session:
        result = await session.execute(
            select(User.reputation_score).where(User.id == user_id)
        )
        return result.scalar_one_or_none() or 0.0

# In workflow:
reputation = await workflow.execute_local_activity(
    get_user_reputation_local,
    user_id,
    schedule_to_close_timeout=timedelta(seconds=1)
)
```

#### 1.5 Search Attributes (`app/config.py` + workflow definitions)
**Purpose**: Query workflows by custom attributes (user_id, status, score)  
**Status**: ⏸️ Planned

**Search Attributes**:
- `user_id` (Int): Find all workflows for a user
- `verification_status` (Keyword): Filter by status (pending, complete, cancelled)
- `target_score` (Double): Find users targeting specific scores
- `created_at` (Datetime): Time-based queries

**Configuration** (Temporal Server):
```bash
temporal operator search-attribute create \
  --name user_id --type Int \
  --name verification_status --type Keyword \
  --name target_score --type Double \
  --name created_at --type Datetime
```

**Usage in Workflows**:
```python
# Set search attributes when starting workflow
handle = await client.start_workflow(
    VerificationWorkflow.run,
    input,
    id=f"verification-{user_id}",
    task_queue="verification-queue",
    search_attributes={
        "user_id": user_id,
        "verification_status": "pending",
        "target_score": input.target_score,
        "created_at": datetime.now()
    }
)

# Query workflows
results = await client.list_workflows(
    "user_id = 123 AND verification_status = 'pending'"
)
```

**Benefits**:
- Find all workflows for a user instantly
- Monitor verification pipeline (how many pending/complete)
- Analytics on verification patterns

---

### Phase 2: Production Hardening (Week 2)

#### 2.1 Heartbeating for Long Activities
**Purpose**: Track progress and detect stalled activities  
**Use Case**: Document processing (OCR, ML validation) can take 10-60 seconds

**Implementation**:
```python
@activity.defn
async def process_document_ocr(user_id: int, document_url: str) -> dict:
    """Process document with OCR, report progress via heartbeating."""
    total_pages = get_page_count(document_url)
    
    for page in range(total_pages):
        # Check for cancellation
        if activity.is_cancelled():
            raise activity.CancelledError("Processing cancelled")
        
        # Process page
        result = await ocr_page(document_url, page)
        
        # Heartbeat with progress
        activity.heartbeat({
            "page": page + 1,
            "total": total_pages,
            "progress_pct": ((page + 1) / total_pages) * 100
        })
    
    return {"status": "complete", "pages": total_pages}

# In workflow with heartbeat timeout:
result = await workflow.execute_activity(
    process_document_ocr,
    user_id,
    document_url,
    start_to_close_timeout=timedelta(minutes=5),
    heartbeat_timeout=timedelta(seconds=30),  # Fail if no heartbeat for 30s
    retry_policy=RetryPolicy(maximum_attempts=3)
)
```

**Benefits**:
- Detect worker crashes/network issues immediately
- Resume from last heartbeat on retry (idempotency)
- Real-time progress visibility

#### 2.2 Cron Schedules
**Purpose**: Automated periodic tasks without external cron  
**Use Cases**:
- Daily reputation recalculation (all users)
- Weekly verification reminders (incomplete users)
- Monthly trust network updates

**Implementation**:
```python
# Start scheduled workflow
await client.create_schedule(
    id="daily-reputation-update",
    schedule=Schedule(
        spec=ScheduleSpec(
            cron_expressions=["0 2 * * *"],  # 2 AM daily
            timezone="America/Los_Angeles"
        ),
        action=ScheduleActionStartWorkflow(
            ReputationBatchUpdateWorkflow.run,
            args=(),
            id_prefix="reputation-update-",
            task_queue="reputation-queue"
        )
    ),
    policy=SchedulePolicy(
        overlap=ScheduleOverlapPolicy.SKIP,  # Skip if previous still running
        catchup_window=timedelta(hours=1)  # Only catch up within 1 hour
    )
)
```

**Benefits**:
- No external cron service needed
- Automatic failure handling and retries
- Visibility in Temporal UI
- Pause/resume schedules without code changes

#### 2.3 Custom Data Converters (Pydantic)
**Purpose**: Type-safe serialization of Pydantic models  
**Status**: ⏸️ Planned

**Implementation**:
```python
from temporalio.contrib.pydantic import pydantic_data_converter

# Configure client with Pydantic converter
client = await Client.connect(
    "localhost:7233",
    data_converter=pydantic_data_converter
)

# Now Pydantic models serialize automatically
@dataclass
class VerificationInput:
    user_id: int
    target_score: float
    initial_methods: list[str] = field(default_factory=list)

# Works automatically with Pydantic converter
result = await client.execute_workflow(
    VerificationWorkflow.run,
    VerificationInput(user_id=123, target_score=60.0),
    id="verification-123",
    task_queue="verification-queue"
)
```

---

### Phase 3: Advanced Patterns (Week 3)

#### 3.1 Saga Pattern (Distributed Transactions)
**Use Case**: Matching workflow that reserves opportunity slots, updates user assignments, sends notifications (all must succeed or rollback)

**Implementation**:
```python
@workflow.defn
class MatchingWorkflow:
    """Saga pattern for matching with compensation."""
    
    @workflow.run
    async def run(self, user_id: int, opportunity_id: int) -> dict:
        compensations = []
        
        try:
            # Step 1: Reserve opportunity slot
            await workflow.execute_activity(
                reserve_opportunity_slot,
                opportunity_id,
                user_id,
                start_to_close_timeout=timedelta(seconds=30)
            )
            compensations.append(
                lambda: workflow.execute_activity(
                    release_opportunity_slot,
                    opportunity_id,
                    user_id,
                    start_to_close_timeout=timedelta(seconds=30)
                )
            )
            
            # Step 2: Update user assignment
            await workflow.execute_activity(
                assign_user_to_opportunity,
                user_id,
                opportunity_id,
                start_to_close_timeout=timedelta(seconds=30)
            )
            compensations.append(
                lambda: workflow.execute_activity(
                    remove_user_assignment,
                    user_id,
                    opportunity_id,
                    start_to_close_timeout=timedelta(seconds=30)
                )
            )
            
            # Step 3: Send notifications
            await workflow.execute_activity(
                send_match_notification,
                user_id,
                opportunity_id,
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return {"status": "matched", "user_id": user_id, "opportunity_id": opportunity_id}
            
        except Exception as e:
            # Compensate in reverse order
            workflow.logger.warning(f"Match failed, compensating: {e}")
            for compensation in reversed(compensations):
                try:
                    await compensation()
                except Exception as comp_error:
                    workflow.logger.error(f"Compensation failed: {comp_error}")
            
            raise
```

**Benefits**:
- Automatic rollback on failure
- Distributed transaction semantics
- No orphaned/inconsistent state

#### 3.2 Workflow Versioning
**Purpose**: Deploy new workflow versions without breaking running workflows  
**Use Case**: Update verification scoring algorithm while old workflows complete with old logic

**Pattern**:
```python
@workflow.defn
class VerificationWorkflow:
    @workflow.run
    async def run(self, input: VerificationInput) -> VerificationResult:
        # Version check using workflow.patch()
        version = workflow.patch("scoring-algorithm-v2")
        
        if version:
            # New scoring algorithm (v2)
            score = await workflow.execute_activity(
                calculate_verification_score_v2,
                self._user_id,
                self._methods_completed,
                start_to_close_timeout=timedelta(seconds=30)
            )
        else:
            # Old scoring algorithm (v1) for existing workflows
            score = await workflow.execute_activity(
                calculate_verification_score,
                self._user_id,
                self._methods_completed,
                start_to_close_timeout=timedelta(seconds=30)
            )
        
        return score
```

**Benefits**:
- Zero-downtime deployments
- Gradual rollout of workflow changes
- Replay compatibility maintained

---

## Configuration Changes Required

### 1. Update `app/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Temporal Advanced Features
    temporal_search_attributes_enabled: bool = True
    temporal_schedules_enabled: bool = True
    temporal_interceptors_enabled: bool = True
    temporal_metrics_backend: str = "prometheus"  # or "statsd", "datadog"
    temporal_metrics_port: int = 9090
```

### 2. Update `app/worker.py`
```python
from app.core.interceptors import LoggingInterceptor, MetricsInterceptor
from temporalio.contrib.pydantic import pydantic_data_converter

async def main():
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        data_converter=pydantic_data_converter,  # Pydantic support
    )
    
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[VerificationWorkflow, ReputationDecayWorkflow],
        activities=[...],
        interceptors=[LoggingInterceptor(), MetricsInterceptor()],  # Observability
        max_concurrent_activities=100,
        max_concurrent_workflow_tasks=50,
    )
    
    await worker.run()
```

### 3. Update `docker-compose.yaml`
```yaml
services:
  temporal:
    # ... existing config ...
    command:
      - "temporal"
      - "server"
      - "start-dev"
      - "--search-attribute"
      - "user_id=Int"
      - "--search-attribute"
      - "verification_status=Keyword"
      - "--search-attribute"
      - "target_score=Double"
```

---

## Testing Strategy

### 1. Time-Skipping Tests (Already Partially Used)
```python
async def test_verification_workflow_with_timeout():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(env.client, task_queue="test-queue", workflows=[VerificationWorkflow]):
            # Start workflow
            handle = await env.client.start_workflow(
                VerificationWorkflow.run,
                VerificationInput(user_id=123, target_score=60.0, timeout_days=30),
                id="test-verification",
                task_queue="test-queue"
            )
            
            # Fast-forward 30 days
            await env.sleep(timedelta(days=30))
            
            # Verify timeout
            result = await handle.result()
            assert result.status == "timeout"
```

### 2. Activity Mocking
```python
async def test_workflow_with_mocked_activities():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Mock expensive activities
        async def mock_calculate_score(user_id, methods):
            return 75.0
        
        env.mock_activity(calculate_verification_score, mock_calculate_score)
        
        # Test workflow logic without real activities
        result = await env.client.execute_workflow(...)
        assert result.final_score == 75.0
```

---

## Metrics & Monitoring

### Prometheus Metrics (via MetricsInterceptor)
- `temporal_workflow_started_total{workflow_type="VerificationWorkflow"}`
- `temporal_workflow_completed_total{workflow_type="VerificationWorkflow",status="success"}`
- `temporal_workflow_duration_seconds{workflow_type="VerificationWorkflow",quantile="0.99"}`
- `temporal_activity_started_total{activity_name="calculate_verification_score"}`
- `temporal_activity_retry_total{activity_name="send_notification"}`

### Logging Structure
```json
{
  "timestamp": "2025-10-29T20:00:00Z",
  "level": "INFO",
  "message": "[Workflow Start] VerificationWorkflow",
  "workflow_id": "verification-123",
  "run_id": "abc-def-456",
  "user_id": 123,
  "target_score": 60.0
}
```

---

## Migration Path

### Current State (Task 4 - 80% Complete)
- ✅ Basic workflows with signals/queries
- ✅ Retry policies configured
- ✅ Activities for verification steps
- ✅ Database integration
- ⏸️ No interceptors, search attributes, or schedules

### Target State (Task 6 Complete)
- ✅ Interceptors for logging/metrics
- ✅ Search attributes for querying
- ✅ Child workflows for complex verification
- ✅ Continue-as-new for reputation decay
- ✅ Local activities for fast reads
- ✅ Cron schedules for batch jobs
- ✅ Heartbeating for long activities
- ✅ Pydantic data converters
- ⏸️ Saga pattern (Phase 3)
- ⏸️ Workflow versioning (Phase 3)

### Rollout Strategy
1. **Week 1**: Implement interceptors, search attributes, local activities (low risk)
2. **Week 2**: Add child workflows, schedules, heartbeating (medium risk, test thoroughly)
3. **Week 3**: Implement saga pattern, versioning (high risk, gradual rollout)

---

## Resources

### Documentation
- Temporal Python SDK: https://github.com/temporalio/sdk-python
- Workflow Patterns: https://docs.temporal.io/workflows
- Search Attributes: https://docs.temporal.io/visibility
- Interceptors: https://docs.temporal.io/interceptors

### Examples
- Context7 `/temporalio/sdk-python`: 20,000 tokens reviewed
- Workflow examples with child workflows, continue-as-new, versioning
- Activity examples with heartbeating, local activities, timeouts
- Interceptor examples with logging, metrics, authentication

### Team Knowledge
- All Temporal features verified against Context7 documentation
- Pydantic data converters: `temporalio.contrib.pydantic`
- Time-skipping tests: `WorkflowEnvironment.start_time_skipping()`
- Heartbeating: `activity.heartbeat()` with details
- Continue-as-new: `workflow.continue_as_new()` for long-running workflows

---

## Next Steps

1. ✅ **Read Context7 documentation** (DONE)
2. 🚧 **Create interceptors** (`app/core/interceptors.py`) - IN PROGRESS
3. ⏸️ **Configure search attributes** (Temporal server + docker-compose.yaml)
4. ⏸️ **Implement child workflows** (`app/workflows/verification_subworkflows.py`)
5. ⏸️ **Add local activities** (`app/activities/local.py`)
6. ⏸️ **Create reputation decay workflow** with continue-as-new (`app/workflows/reputation.py`)
7. ⏸️ **Set up cron schedules** for batch jobs
8. ⏸️ **Add heartbeating** to long activities (document processing)
9. ⏸️ **Enable Pydantic data converter** in worker
10. ⏸️ **Write comprehensive tests** with time-skipping

**Estimated Completion**: 3 weeks (Phases 1-3)  
**Priority Focus**: Phase 1 (Week 1) - Interceptors, search attributes, local activities
