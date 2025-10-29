"""Verification API endpoints.

Endpoints for starting verification workflows, completing verification methods,
and querying verification status.
"""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client

from app.config import Settings, settings
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.verification import (
    StartVerificationRequest,
    VerificationMethodRequest,
    VerificationScoreResponse,
    VerificationStatusResponse,
)
from app.workflows.verification import VerificationInput, VerificationWorkflow

router = APIRouter(prefix="/verification", tags=["verification"])


async def get_temporal_client() -> Client:
    """Get Temporal client connection.

    Returns:
        Connected Temporal client.

    Raises:
        HTTPException: If unable to connect to Temporal server.
    """
    try:
        return await Client.connect(
            settings.temporal_host, namespace=settings.temporal_namespace
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to connect to Temporal server: {e}",
        )


@router.post("/start", response_model=VerificationStatusResponse, status_code=201)
async def start_verification(
    request: StartVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    temporal: Annotated[Client, Depends(get_temporal_client)],
) -> VerificationStatusResponse:
    """Start verification workflow for a user.

    Args:
        request: Verification start request with user_id and target_score.
        db: Database session.
        current_user: Authenticated user making the request.
        temporal: Temporal client.

    Returns:
        Verification status response with workflow ID.

    Raises:
        HTTPException: If user not found or workflow already running.

    Example:
        POST /api/v1/verification/start
        {
            "user_id": 123,
            "target_score": 60.0,
            "timeout_days": 30
        }
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if workflow already running
    if user.verification_workflow_id:
        try:
            # Query existing workflow to see if still running
            handle = temporal.get_workflow_handle(user.verification_workflow_id)
            current_score = await handle.query(VerificationWorkflow.current_score)
            progress = await handle.query(VerificationWorkflow.progress_percentage)
            methods = await handle.query(VerificationWorkflow.methods_completed)

            return VerificationStatusResponse(
                user_id=user.id,
                workflow_id=user.verification_workflow_id,
                current_score=current_score,
                target_score=request.target_score,
                progress_percentage=progress,
                methods_completed=methods,
                status="running",
            )
        except Exception:
            # Workflow not running, proceed with new one
            pass

    # Start new verification workflow
    workflow_id = f"verification-{user.id}"
    workflow_input = VerificationInput(
        user_id=user.id,
        initial_methods=[],
        target_score=request.target_score,
        timeout_days=request.timeout_days,
    )

    try:
        handle = await temporal.start_workflow(
            VerificationWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=settings.temporal_verification_queue,
        )

        # Update user with workflow ID
        user.verification_workflow_id = workflow_id
        await db.commit()

        return VerificationStatusResponse(
            user_id=user.id,
            workflow_id=workflow_id,
            current_score=user.verification_score,
            target_score=request.target_score,
            progress_percentage=0.0,
            methods_completed=[],
            status="running",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start verification workflow: {e}",
        )


@router.post("/complete-method/{user_id}")
async def complete_verification_method(
    user_id: int,
    request: VerificationMethodRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    temporal: Annotated[Client, Depends(get_temporal_client)],
) -> dict:
    """Signal completion of a verification method.

    Args:
        user_id: ID of user completing verification.
        request: Verification method details.
        db: Database session.
        current_user: Authenticated user making the request.
        temporal: Temporal client.

    Returns:
        Success message with updated score.

    Raises:
        HTTPException: If user not found or no active workflow.

    Example:
        POST /api/v1/verification/complete-method/123
        {
            "method": "community",
            "weight": 20.0,
            "evidence": {"validator_id": 456}
        }
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for active workflow
    if not user.verification_workflow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification workflow. Start verification first.",
        )

    try:
        # Signal workflow
        handle = temporal.get_workflow_handle(user.verification_workflow_id)
        await handle.signal(
            "complete_verification_method",
            request.method,
            request.weight,
            request.evidence,
        )

        # Query updated score
        current_score = await handle.query("current_score")

        return {
            "message": "Verification method completed successfully",
            "method": request.method,
            "current_score": current_score,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to signal workflow: {e}",
        )


@router.get("/status/{user_id}", response_model=VerificationStatusResponse)
async def get_verification_status(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    temporal: Annotated[Client, Depends(get_temporal_client)],
) -> VerificationStatusResponse:
    """Get current verification status for a user.

    Args:
        user_id: ID of user to check.
        db: Database session.
        current_user: Authenticated user making the request.
        temporal: Temporal client.

    Returns:
        Verification status with current score and progress.

    Raises:
        HTTPException: If user not found or no workflow.

    Example:
        GET /api/v1/verification/status/123
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for workflow
    if not user.verification_workflow_id:
        # Return current state from database
        methods = (
            json.loads(user.verification_methods) if user.verification_methods else []
        )
        return VerificationStatusResponse(
            user_id=user.id,
            workflow_id="",
            current_score=user.verification_score,
            target_score=user.verification_score,
            progress_percentage=100.0 if user.verification_score > 0 else 0.0,
            methods_completed=methods,
            status="not_started",
        )

    try:
        # Query workflow
        handle = temporal.get_workflow_handle(user.verification_workflow_id)
        current_score = await handle.query("current_score")
        progress = await handle.query("progress_percentage")
        methods = await handle.query("methods_completed")

        # Try to determine status (workflow still running if queries succeed)
        workflow_status = "running"
        try:
            result = await handle.result()
            workflow_status = result.status
        except Exception:
            # Workflow still running
            pass

        return VerificationStatusResponse(
            user_id=user.id,
            workflow_id=user.verification_workflow_id,
            current_score=current_score,
            target_score=50.0,  # Default target, could be stored
            progress_percentage=progress,
            methods_completed=methods,
            status=workflow_status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query workflow: {e}",
        )


@router.post("/cancel/{user_id}")
async def cancel_verification(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    temporal: Annotated[Client, Depends(get_temporal_client)],
) -> dict:
    """Cancel active verification workflow.

    Args:
        user_id: ID of user to cancel verification for.
        db: Database session.
        current_user: Authenticated user making the request.
        temporal: Temporal client.

    Returns:
        Success message.

    Raises:
        HTTPException: If user not found or no active workflow.

    Example:
        POST /api/v1/verification/cancel/123
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for active workflow
    if not user.verification_workflow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification workflow",
        )

    try:
        # Signal cancellation
        handle = temporal.get_workflow_handle(user.verification_workflow_id)
        await handle.signal("cancel_verification")

        # Clear workflow ID
        user.verification_workflow_id = None
        await db.commit()

        return {"message": "Verification workflow cancelled successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {e}",
        )


@router.get("/score/{user_id}", response_model=VerificationScoreResponse)
async def get_verification_score(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> VerificationScoreResponse:
    """Get user's verification score breakdown.

    Args:
        user_id: ID of user to check.
        db: Database session.
        current_user: Authenticated user making the request.

    Returns:
        Verification score breakdown with methods and timestamps.

    Raises:
        HTTPException: If user not found.

    Example:
        GET /api/v1/verification/score/123
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Parse verification methods
    methods = json.loads(user.verification_methods) if user.verification_methods else []

    return VerificationScoreResponse(
        user_id=user.id,
        verification_score=user.verification_score,
        activity_score=user.activity_score,
        methods=methods,
        last_updated=user.updated_at,
    )
