"""Verification API schemas for request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VerificationMethodRequest(BaseModel):
    """Request to complete a verification method.

    Attributes:
        method: Type of verification (document, community, in_person, trust_network, activity).
        weight: Score weight for this method (0-100).
        evidence: Method-specific evidence data.
    """

    method: str = Field(..., description="Verification method type")
    weight: float = Field(..., ge=0, le=100, description="Score weight (0-100)")
    evidence: dict[str, Any] = Field(default_factory=dict, description="Evidence data")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "community",
                    "weight": 20.0,
                    "evidence": {"validator_id": 456, "notes": "Verified in-person"},
                }
            ]
        }
    }


class StartVerificationRequest(BaseModel):
    """Request to start verification workflow.

    Attributes:
        user_id: ID of user to verify.
        target_score: Target verification score (default 50, max 100).
        timeout_days: Maximum days to wait for verification (default 30).
    """

    user_id: int = Field(..., description="User ID to verify")
    target_score: float = Field(
        default=50.0, ge=0, le=100, description="Target score (0-100)"
    )
    timeout_days: int = Field(
        default=30, ge=1, le=365, description="Timeout in days (1-365)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"user_id": 123, "target_score": 60.0, "timeout_days": 30}]
        }
    }


class VerificationStatusResponse(BaseModel):
    """Response with current verification status.

    Attributes:
        user_id: User ID.
        workflow_id: Temporal workflow ID.
        current_score: Current verification score (0-100).
        target_score: Target verification score.
        progress_percentage: Progress towards target (0-100).
        methods_completed: List of completed verification methods.
        status: Workflow status (running, completed, timeout, cancelled).
    """

    user_id: int
    workflow_id: str
    current_score: float = Field(..., ge=0, le=100)
    target_score: float = Field(..., ge=0, le=100)
    progress_percentage: float = Field(..., ge=0, le=100)
    methods_completed: list[dict[str, Any]]
    status: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 123,
                    "workflow_id": "verification-123",
                    "current_score": 35.0,
                    "target_score": 60.0,
                    "progress_percentage": 58.33,
                    "methods_completed": [
                        {
                            "method": "community",
                            "weight": 20.0,
                            "completed_at": "2025-10-29T17:30:00Z",
                        },
                        {
                            "method": "activity",
                            "weight": 15.0,
                            "completed_at": "2025-10-29T18:00:00Z",
                        },
                    ],
                    "status": "running",
                }
            ]
        }
    }


class TrustConnectionRequest(BaseModel):
    """Request to add a trust network connection.

    Attributes:
        trusted_user_id: ID of user to add to trust network.
        strength: Trust strength (0.0-1.0).
        notes: Optional notes about the connection.
    """

    trusted_user_id: int = Field(..., description="User ID to trust")
    strength: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Trust strength (0.0-1.0)"
    )
    notes: str | None = Field(
        None, max_length=500, description="Optional notes about connection"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "trusted_user_id": 456,
                    "strength": 0.9,
                    "notes": "Worked together on community project",
                }
            ]
        }
    }


class VerificationScoreResponse(BaseModel):
    """Response with user's verification score breakdown.

    Attributes:
        user_id: User ID.
        verification_score: Total verification score (0-100).
        activity_score: Score from volunteer activity.
        methods: List of completed verification methods with weights.
        last_updated: Timestamp of last score update.
    """

    user_id: int
    verification_score: float = Field(..., ge=0, le=100)
    activity_score: float = Field(..., ge=0, le=100)
    methods: list[dict[str, Any]]
    last_updated: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 123,
                    "verification_score": 65.0,
                    "activity_score": 15.0,
                    "methods": [
                        {"method": "community", "weight": 20.0},
                        {"method": "trust_network", "weight": 10.0},
                        {"method": "in_person", "weight": 35.0},
                    ],
                    "last_updated": "2025-10-29T18:30:00Z",
                }
            ]
        }
    }
