# Identity Verification System - Implementation Guide

## Overview

The Voluntier identity verification system implements a **scaled verification approach (0-100)** instead of binary yes/no verification. This design prioritizes accessibility - **email is NOT required**, and users can verify through any combination of methods.

## Core Philosophy

- **Inclusive**: No single method is required (no email, no government ID, no conventional documents)
- **Scaled**: 0-100 score accumulated through multiple pathways
- **Durable**: Temporal workflows provide fault-tolerant, long-running orchestration
- **Flexible**: Multiple verification pathways that are not mutually exclusive

## Verification Pathways

Users can accumulate verification points through any combination of:

| Method | Points | Description | Evidence |
|--------|--------|-------------|----------|
| **Document Upload** | 20-30 | Government ID, utility bills, official documents | Scanned documents, OCR verification |
| **Community Validation** | 15-25 per voucher (max 50) | Verified users vouch for new users | Voucher user_id, relationship notes |
| **In-Person Verification** | 30-40 | Verification at community centers, events | Location, date, verifier_id |
| **Trust Network** | 5-15 | Connections to verified users | Trusted user_id, connection strength |
| **Activity History** | 10-20 | Successful volunteer hours, reviews | Hours completed, review scores |

**Target Score**: Default 50 (customizable per user)

## Architecture

### Temporal Workflows

The verification system uses Temporal for durable workflow orchestration:

- **VerificationWorkflow**: Long-running process (up to 30 days)
- **Signals**: Real-time updates (complete_verification_method, update_trust_network, cancel_verification)
- **Queries**: Progress monitoring (current_score, methods_completed, progress_percentage)
- **Activities**: Individual verification operations (idempotent, retryable)

### Database Schema

User model changes:
```python
# REMOVED (binary flags):
verification_status: str
document_verified: bool
community_verified: bool
in_person_verified: bool

# ADDED (scaled scoring):
verification_score: float  # 0-100
verification_methods: str | None  # JSON array
verification_workflow_id: str | None  # Temporal workflow ID
trust_network: str | None  # JSON array of vouchers
activity_score: float  # Activity-based score

# CHANGED:
email: str | None  # Now optional (was required)
```

## Setup Instructions

### 1. Run Database Migration

```bash
# Apply schema changes
uv run alembic upgrade head

# Verify migration
uv run alembic current
# Should show: a6e983422c84 (head)
```

### 2. Start Temporal Server

**Option A: Temporal CLI (Development)**
```bash
# Install Temporal CLI if not already installed
brew install temporal

# Start development server with UI
temporal server start-dev

# Server will run on:
# - Temporal API: localhost:7233
# - Web UI: http://localhost:8233
```

**Option B: Docker (Alternative)**
```bash
docker run -d -p 7233:7233 -p 8233:8233 \
  --name temporal-dev \
  temporalio/auto-setup:latest
```

### 3. Start Temporal Worker

The worker processes workflows and executes activities:

```bash
# Terminal 2
uv run python -m app.worker

# Expected output:
# INFO: Connected to Temporal server at localhost:7233
# INFO: Namespace: default
# INFO: Task queue: verification-queue
# INFO: Worker started successfully!
# INFO: Registered workflows: VerificationWorkflow
# INFO: Registered activities: calculate_verification_score, ...
# INFO: Listening for workflows and activities...
```

**Keep this running** - it processes verification workflows in the background.

### 4. Start FastAPI Server

```bash
# Terminal 3
uv run fastapi dev main.py

# API available at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## API Usage Examples

### 1. Register and Login

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "volunteer@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Smith"
  }'

# Login to get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=volunteer@example.com&password=SecurePass123!'

# Response:
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "token_type": "bearer"
# }

# Export token for subsequent requests
export TOKEN="eyJ0eXAi..."
```

### 2. Start Verification Workflow

```bash
curl -X POST http://localhost:8000/api/v1/verification/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "target_score": 60.0,
    "timeout_days": 30
  }'

# Response:
# {
#   "user_id": 1,
#   "workflow_id": "verification-1",
#   "current_score": 0.0,
#   "target_score": 60.0,
#   "progress_percentage": 0.0,
#   "methods_completed": [],
#   "status": "running"
# }
```

### 3. Complete Verification Methods

```bash
# Complete community validation
curl -X POST http://localhost:8000/api/v1/verification/complete-method/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "community",
    "weight": 20.0,
    "evidence": {
      "validator_id": 2,
      "notes": "Verified at community event",
      "date": "2025-10-29"
    }
  }'

# Complete document upload
curl -X POST http://localhost:8000/api/v1/verification/complete-method/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "document",
    "weight": 25.0,
    "evidence": {
      "document_type": "utility_bill",
      "document_id": "scan-12345.pdf",
      "verified_by": "ocr_service"
    }
  }'

# Complete in-person verification
curl -X POST http://localhost:8000/api/v1/verification/complete-method/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "in_person",
    "weight": 35.0,
    "evidence": {
      "location": "Community Center A",
      "verifier_id": 3,
      "date": "2025-10-29"
    }
  }'

# Response:
# {
#   "message": "Verification method completed successfully",
#   "method": "in_person",
#   "current_score": 80.0
# }
```

### 4. Check Verification Status

```bash
curl http://localhost:8000/api/v1/verification/status/1 \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "user_id": 1,
#   "workflow_id": "verification-1",
#   "current_score": 80.0,
#   "target_score": 60.0,
#   "progress_percentage": 133.33,
#   "methods_completed": [
#     {
#       "method": "community",
#       "weight": 20.0,
#       "completed_at": "2025-10-29T17:30:00Z",
#       "evidence": {...}
#     },
#     {
#       "method": "document",
#       "weight": 25.0,
#       "completed_at": "2025-10-29T17:35:00Z",
#       "evidence": {...}
#     },
#     {
#       "method": "in_person",
#       "weight": 35.0,
#       "completed_at": "2025-10-29T17:40:00Z",
#       "evidence": {...}
#     }
#   ],
#   "status": "completed"
# }
```

### 5. Get Score Breakdown

```bash
curl http://localhost:8000/api/v1/verification/score/1 \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "user_id": 1,
#   "verification_score": 80.0,
#   "activity_score": 0.0,
#   "methods": [
#     {"method": "community", "weight": 20.0},
#     {"method": "document", "weight": 25.0},
#     {"method": "in_person", "weight": 35.0}
#   ],
#   "last_updated": "2025-10-29T17:40:00Z"
# }
```

### 6. Cancel Verification (Optional)

```bash
curl -X POST http://localhost:8000/api/v1/verification/cancel/1 \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "message": "Verification workflow cancelled successfully"
# }
```

## Monitoring Workflows

### Temporal Web UI

Visit: http://localhost:8233

- View all running workflows
- Inspect workflow history
- Query current state
- View activity execution logs
- Debug failed workflows

### Temporal CLI

```bash
# List workflows
temporal workflow list

# Describe specific workflow
temporal workflow describe --workflow-id verification-1

# Query workflow
temporal workflow query \
  --workflow-id verification-1 \
  --type current_score

# Signal workflow (alternative to API)
temporal workflow signal \
  --workflow-id verification-1 \
  --name complete_verification_method \
  --input '{"method": "community", "weight": 20.0, "evidence": {}}'
```

## Testing

### Integration Tests (TODO)

```python
# tests/test_verification_workflow.py
import pytest
from temporalio.testing import WorkflowEnvironment
from app.workflows.verification import VerificationWorkflow, VerificationInput

async def test_verification_workflow():
    """Test complete verification workflow with time skipping."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[VerificationWorkflow],
            activities=[...],
        ):
            # Start workflow
            result = await env.client.execute_workflow(
                VerificationWorkflow.run,
                VerificationInput(user_id=1, target_score=50.0),
                id="test-verification-1",
                task_queue="test-queue",
            )
            
            # Signal method completion
            handle = env.client.get_workflow_handle("test-verification-1")
            await handle.signal("complete_verification_method", "community", 20.0, {})
            
            # Query current score
            score = await handle.query("current_score")
            assert score == 20.0
```

### Manual Testing Checklist

- [ ] Start verification workflow for new user
- [ ] Complete multiple verification methods
- [ ] Query progress at each step
- [ ] Verify score accumulation (0-100 cap)
- [ ] Test workflow timeout (set short timeout for testing)
- [ ] Test workflow cancellation
- [ ] Verify database updates (check users table)
- [ ] Monitor Temporal UI for workflow execution
- [ ] Test error handling (invalid evidence, missing user, etc.)
- [ ] Test trust network score calculation

## Troubleshooting

### "Unable to connect to Temporal server"

**Cause**: Temporal server not running or wrong host/port

**Solution**:
```bash
# Check if Temporal is running
lsof -i :7233

# Start Temporal if not running
temporal server start-dev
```

### "No active verification workflow"

**Cause**: Workflow hasn't been started or already completed

**Solution**:
```bash
# Start new workflow
curl -X POST http://localhost:8000/api/v1/verification/start \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"user_id": 1, "target_score": 50.0}'
```

### "Worker not processing workflows"

**Cause**: Worker not running or listening on wrong queue

**Solution**:
```bash
# Check worker logs
uv run python -m app.worker

# Verify worker is registered on correct queue (verification-queue)
# Check Temporal UI -> Workers tab
```

### "Database migration failed"

**Cause**: Database not running or schema conflict

**Solution**:
```bash
# Check current revision
uv run alembic current

# Roll back if needed
uv run alembic downgrade -1

# Re-apply migration
uv run alembic upgrade head

# If major issues, reset database (CAUTION: data loss)
uv run alembic downgrade base
uv run alembic upgrade head
```

## Next Steps

1. **Complete Task 4**:
   - [ ] Run database migration
   - [ ] Start Temporal server + worker
   - [ ] Write integration tests with time skipping
   - [ ] Document verification pathways in README
   - [ ] Test complete user flow (register → verify → check score)

2. **Production Considerations**:
   - [ ] Deploy Temporal server cluster (or use Temporal Cloud)
   - [ ] Deploy Temporal worker as systemd service or Docker container
   - [ ] Add field-level encryption for PII in evidence data
   - [ ] Implement document upload storage (S3, CloudFlare R2)
   - [ ] Add OCR service integration for document verification
   - [ ] Set up monitoring and alerting for workflow failures
   - [ ] Configure workflow retention policy
   - [ ] Add rate limiting for verification endpoints

3. **Feature Enhancements**:
   - [ ] Implement trust network visualization
   - [ ] Add verification method recommendations based on user profile
   - [ ] Create admin dashboard for verification oversight
   - [ ] Add appeal/dispute process for rejected verifications
   - [ ] Implement automated fraud detection
   - [ ] Add verification badge levels (Bronze 25-49, Silver 50-74, Gold 75-100)

## Key Decisions

### Why Temporal?

- **Durability**: Workflows survive crashes and restarts
- **Observability**: Built-in UI for monitoring and debugging
- **Reliability**: Automatic retries with exponential backoff
- **Scalability**: Horizontal scaling with multiple workers
- **Time-based logic**: Native support for timeouts and schedules

### Why Scaled Verification?

- **Inclusivity**: No single method required (no email, no government ID)
- **Flexibility**: Users can choose verification paths that work for them
- **Gradual trust**: Trust builds incrementally, not as binary gate
- **Accessibility**: People without conventional IDs can still participate
- **Recovery**: Low scores can be improved over time

### Why No Email Requirement?

Per project requirements: "Email should **not** be required, nor should any other form of identity verification. There should be a way for people with no conventional way to prove their identity to become verified."

This aligns with the core mission of accessibility and inclusivity.

## References

- Temporal Python SDK: https://docs.temporal.io/develop/python
- FastAPI: https://fastapi.tiangolo.com
- Alembic: https://alembic.sqlalchemy.org
- PRD: `/PRD.md` (Phase 1 identity verification requirements)
- GitHub: https://github.com/1withall/voluntier
