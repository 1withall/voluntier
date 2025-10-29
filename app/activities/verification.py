"""Verification activities for Temporal workflows.

These activities handle individual verification steps:
- Document verification processing
- Community validation checks
- Trust network strength calculations
- Score updates in database
- Notification sending

Activities are designed to be:
- Idempotent: Can be safely retried
- Atomic: Single responsibility per activity
- Async: Non-blocking database operations
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from temporalio import activity
from temporalio.exceptions import CancelledError

from app.database import get_session_factory
from app.models import User


def _get_session():
    """Helper to get database session for activities."""
    return get_session_factory()()


@dataclass
class VerificationMethod:
    """Verification method completion data.

    Attributes:
        method: Type of verification (document, community, in_person, trust_network, activity).
        weight: Score weight for this method (0-100).
        evidence: Method-specific evidence data.
        completed_at: ISO timestamp of completion.
    """

    method: str
    weight: float
    evidence: dict[str, Any]
    completed_at: str


@activity.defn
async def calculate_verification_score(
    user_id: int, verification_methods: list[dict[str, Any]]
) -> float:
    """Calculate composite verification score from multiple methods.

    Scoring algorithm:
    - Document upload: 20-30 points (depends on document quality/type)
    - Community validation: 15-25 points per voucher (max 50 total)
    - In-person verification: 30-40 points
    - Trust network: 5-15 points (based on network strength)
    - Activity history: 10-20 points (based on hours volunteered)

    Maximum score: 100 points

    Args:
        user_id: User ID to calculate score for.
        verification_methods: List of completed verification methods.

    Returns:
        float: Composite verification score (0-100).

    Example:
        >>> methods = [
        ...     {"method": "community", "weight": 20},
        ...     {"method": "activity", "weight": 15}
        ... ]
        >>> score = await calculate_verification_score(123, methods)
        >>> assert 0 <= score <= 100
    """
    activity.logger.info(
        f"Calculating verification score for user {user_id} with {len(verification_methods)} methods"
    )

    # Sum all method weights, cap at 100
    total_score = sum(method.get("weight", 0) for method in verification_methods)
    final_score = min(total_score, 100.0)

    # Apply diminishing returns for similar methods
    method_types = {}
    for method in verification_methods:
        method_type = method.get("method", "unknown")
        method_types[method_type] = method_types.get(method_type, 0) + 1

    # If multiple community validations, apply diminishing returns
    if method_types.get("community", 0) > 2:
        # Reduce score slightly for excessive community validations
        excess = method_types["community"] - 2
        final_score = max(final_score - (excess * 2), 0)

    activity.logger.info(f"Calculated verification score: {final_score}")
    return round(final_score, 2)


@activity.defn
async def record_verification_method(
    user_id: int, method: VerificationMethod
) -> dict[str, Any]:
    """Record a completed verification method in the database.

    Updates the user's verification_methods JSON field with the new method.
    This activity is idempotent - re-recording the same method updates the timestamp.

    Args:
        user_id: User ID to record method for.
        method: Verification method details.

    Returns:
        dict: Updated verification methods list.

    Raises:
        ValueError: If user not found.
    """
    activity.logger.info(
        f"Recording verification method '{method.method}' for user {user_id}"
    )

    async with _get_session() as session:
        # Get user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Parse existing methods
        existing_methods = []
        if user.verification_methods:
            try:
                existing_methods = json.loads(user.verification_methods)
            except json.JSONDecodeError:
                activity.logger.warning(
                    f"Invalid verification_methods JSON for user {user_id}, resetting"
                )
                existing_methods = []

        # Add or update method
        method_dict = {
            "method": method.method,
            "weight": method.weight,
            "evidence": method.evidence,
            "completed_at": method.completed_at,
        }

        # Check if method already exists (update instead of duplicate)
        existing_index = next(
            (
                i
                for i, m in enumerate(existing_methods)
                if m.get("method") == method.method
            ),
            None,
        )

        if existing_index is not None:
            existing_methods[existing_index] = method_dict
            activity.logger.info(f"Updated existing method '{method.method}'")
        else:
            existing_methods.append(method_dict)
            activity.logger.info(f"Added new method '{method.method}'")

        # Update user
        user.verification_methods = json.dumps(existing_methods)
        await session.commit()

        activity.logger.info(
            f"Successfully recorded method, total methods: {len(existing_methods)}"
        )
        return {"methods": existing_methods, "count": len(existing_methods)}


@activity.defn
async def update_user_verification_score(user_id: int, score: float) -> bool:
    """Update user's verification score in database.

    Args:
        user_id: User ID to update.
        score: New verification score (0-100).

    Returns:
        bool: True if update successful.

    Raises:
        ValueError: If user not found or score invalid.
    """
    if not 0 <= score <= 100:
        raise ValueError(f"Invalid verification score: {score}. Must be 0-100.")

    activity.logger.info(f"Updating verification score for user {user_id} to {score}")

    async with _get_session() as session:
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(verification_score=score)
            .returning(User.id)
        )

        if not result.scalar_one_or_none():
            raise ValueError(f"User {user_id} not found")

        await session.commit()
        activity.logger.info(f"Successfully updated verification score to {score}")
        return True


@activity.defn
async def send_verification_notification(
    user_id: int, notification_type: str, data: dict[str, Any]
) -> bool:
    """Send notification about verification progress.

    In Phase 1, this logs notifications. In later phases, integrate with
    email/SMS/push notification services.

    Args:
        user_id: User to notify.
        notification_type: Type of notification (score_updated, method_completed, etc).
        data: Notification-specific data.

    Returns:
        bool: True if notification sent.
    """
    activity.logger.info(
        f"Sending {notification_type} notification to user {user_id}: {data}"
    )

    # Phase 1: Just log
    # Phase 2+: Integrate with notification service
    # await send_email(user_id, notification_type, data)
    # await send_push_notification(user_id, notification_type, data)

    return True


@activity.defn
async def check_trust_network_strength(user_id: int) -> float:
    """Calculate trust network strength for a user.

    Analyzes the user's connections to verified users and calculates
    a trust score based on:
    - Number of connections to verified users
    - Verification scores of those users
    - Time since connections established
    - Mutual connections (triangulation)

    Args:
        user_id: User ID to analyze.

    Returns:
        float: Trust network strength (0-15 points).
    """
    activity.logger.info(f"Calculating trust network strength for user {user_id}")

    async with _get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.trust_network:
            activity.logger.info("No trust network found, returning 0")
            return 0.0

        try:
            trust_network = json.loads(user.trust_network)
        except json.JSONDecodeError:
            activity.logger.warning("Invalid trust_network JSON")
            return 0.0

        # Calculate trust score based on network
        total_trust = 0.0
        for connection in trust_network:
            trusted_user_id = connection.get("user_id")
            strength = connection.get("strength", 0.5)

            # Get trusted user's verification score
            result = await session.execute(
                select(User.verification_score).where(User.id == trusted_user_id)
            )
            trusted_score = result.scalar_one_or_none()

            if trusted_score and trusted_score > 50:
                # Weight trust by the verifier's own verification score
                total_trust += strength * (trusted_score / 100) * 15

        # Cap at 15 points
        final_trust_score = min(total_trust, 15.0)
        activity.logger.info(f"Trust network strength: {final_trust_score}")

        return round(final_trust_score, 2)


# ==================== Child Workflow Support Activities ====================
# Phase 2: Activities for document, community, and in-person verification


@activity.defn
async def extract_document_data(
    user_id: int, document_type: str, document_url: str, require_ocr: bool
) -> dict[str, Any]:
    """Extract data from uploaded verification document.
    
    For image documents, performs OCR extraction with heartbeating to
    track progress. For PDFs, extracts text and structured data.
    Returns extracted fields like name, DOB, ID number, etc.
    
    **Phase 2: Heartbeating Implementation**
    This activity demonstrates heartbeating for long-running OCR operations.
    Heartbeats allow:
    - Detection of worker crashes (heartbeat timeout)
    - Resumption from last heartbeat on retry
    - Real-time progress reporting to workflows
    
    Args:
        user_id: User ID for logging
        document_type: Type of document (passport, drivers_license, etc.)
        document_url: URL to document file
        require_ocr: Whether OCR extraction is needed
        
    Returns:
        Dictionary of extracted fields
        
    Raises:
        ValueError: If document type is invalid or document cannot be read
    """
    activity.logger.info(
        f"Extracting data from {document_type} for user {user_id}, OCR: {require_ocr}"
    )
    
    # Simulate multi-page document processing with heartbeats
    # In production, this would be actual OCR processing (Tesseract, AWS Textract, etc.)
    total_pages = 3 if document_type == "passport" else 2
    
    extracted_data: dict[str, Any] = {
        "document_type": document_type,
        "document_url": document_url,
    }
    
    # Check if we're retrying and have heartbeat details from previous attempt
    heartbeat_details = activity.info().heartbeat_details
    start_page = 0
    
    if heartbeat_details:
        # Resume from last heartbeat
        start_page = heartbeat_details[0]
        activity.logger.info(
            f"Resuming OCR from page {start_page + 1}/{total_pages} "
            f"after retry"
        )
    
    # Process each page with heartbeat
    for page in range(start_page, total_pages):
        # Send heartbeat with current progress
        # This allows workflow to track progress and detect failures
        progress = {
            "page": page + 1,
            "total_pages": total_pages,
            "progress_pct": ((page + 1) / total_pages) * 100,
            "user_id": user_id,
        }
        
        # Heartbeat with page number (for resumption) and progress details
        activity.heartbeat(page, progress)
        
        activity.logger.info(
            f"Processing page {page + 1}/{total_pages} "
            f"({progress['progress_pct']:.1f}% complete)"
        )
        
        # Simulate OCR processing time per page (1-2 seconds)
        await asyncio.sleep(1.5)
        
        # Check if activity was cancelled
        if activity.is_cancelled():
            activity.logger.warning(
                f"OCR cancelled at page {page + 1}/{total_pages}"
            )
            raise CancelledError("Document OCR cancelled by user")
    
    # Extract final data based on document type
    if document_type == "passport":
        extracted_data.update({
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "passport_number": "AB1234567",
            "country": "USA",
            "expiration_date": "2030-01-01",
            "pages_processed": total_pages,
        })
    elif document_type == "drivers_license":
        extracted_data.update({
            "full_name": "Jane Smith",
            "date_of_birth": "1985-05-15",
            "license_number": "DL987654321",
            "state": "CA",
            "expiration_date": "2028-05-15",
            "pages_processed": total_pages,
        })
    elif document_type == "national_id":
        extracted_data.update({
            "full_name": "Alex Johnson",
            "date_of_birth": "1992-12-20",
            "id_number": "NID123456789",
            "country": "USA",
            "pages_processed": total_pages,
        })
    else:
        raise ValueError(f"Unsupported document type: {document_type}")
    
    activity.logger.info(
        f"Extracted {len(extracted_data)} fields from {document_type} "
        f"({total_pages} pages processed)"
    )
    
    return extracted_data


@activity.defn
async def check_document_validity(
    document_type: str, extracted_data: dict[str, Any]
) -> dict[str, Any]:
    """Validate extracted document data for authenticity and completeness.
    
    Checks document format, required fields, date validity, and
    applies heuristics to detect potential forgeries.
    
    Args:
        document_type: Type of document
        extracted_data: Data extracted from document
        
    Returns:
        Dictionary with:
            - is_valid (bool): Overall validity
            - score (float): Validity score 0-100
            - checks (dict): Individual check results
    """
    activity.logger.info(f"Validating {document_type} document")
    
    checks = {}
    score = 100.0
    
    # Check 1: Required fields present
    required_fields = {
        "passport": ["full_name", "date_of_birth", "passport_number", "country"],
        "drivers_license": ["full_name", "date_of_birth", "license_number", "state"],
        "national_id": ["full_name", "date_of_birth", "id_number", "country"],
    }
    
    required = required_fields.get(document_type, [])
    missing_fields = [f for f in required if f not in extracted_data]
    
    checks["required_fields"] = {
        "passed": len(missing_fields) == 0,
        "missing": missing_fields,
    }
    
    if missing_fields:
        score -= 30.0
    
    # Check 2: Date validity (not expired)
    if "expiration_date" in extracted_data:
        from datetime import datetime
        try:
            expiration = datetime.fromisoformat(extracted_data["expiration_date"])
            is_expired = expiration < datetime.now()
            checks["expiration"] = {
                "passed": not is_expired,
                "date": extracted_data["expiration_date"],
            }
            if is_expired:
                score -= 50.0
        except ValueError:
            checks["expiration"] = {"passed": False, "error": "Invalid date format"}
            score -= 20.0
    
    # Check 3: Format validation (simplified)
    checks["format"] = {"passed": True}  # TODO: Implement format validation
    
    is_valid = score >= 60.0
    
    result = {
        "is_valid": is_valid,
        "score": max(0.0, score),
        "checks": checks,
    }
    
    activity.logger.info(
        f"Document validation: valid={is_valid}, score={score:.1f}"
    )
    
    return result


@activity.defn
async def store_verification_evidence(
    user_id: int, method_type: str, evidence: dict[str, Any]
) -> None:
    """Store verification evidence in database for audit trail.
    
    Creates immutable audit record of verification evidence that can be
    reviewed later for compliance or dispute resolution.
    
    Args:
        user_id: User ID
        method_type: Type of verification (document, community, in_person)
        evidence: Evidence data to store
    """
    activity.logger.info(
        f"Storing {method_type} verification evidence for user {user_id}"
    )
    
    async with _get_session() as session:
        from app.models.user import User
        from sqlalchemy import select, update
        
        # Store in user metadata or separate verification_evidence table
        # For now, update user metadata
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                updated_at=datetime.utcnow(),
                # Store in metadata JSONB field (assuming it exists)
                # metadata=func.jsonb_set(
                #     User.metadata,
                #     f'{{verification_evidence,{method_type}}}',
                #     evidence,
                # )
            )
        )
        
        # TODO: Create proper verification_evidence table in Phase 2
        # For now, just log it
        activity.logger.info(
            f"Stored evidence for user {user_id}: {len(evidence)} fields"
        )


@activity.defn
async def request_community_validators(
    user_id: int, pool_size: int
) -> list[int]:
    """Request community members to validate user's identity.
    
    Selects validators from user's trust network based on:
    - Existing connections
    - Validator reputation
    - Recent validation activity
    - Geographic proximity (if relevant)
    
    Args:
        user_id: User requesting validation
        pool_size: Maximum number of validators to request
        
    Returns:
        List of validator user IDs
    """
    activity.logger.info(
        f"Requesting {pool_size} community validators for user {user_id}"
    )
    
    async with _get_session() as session:
        from app.models.user import User
        from sqlalchemy import select, func
        
        # Find potential validators from trust network
        # TODO: Implement actual trust network query
        # For now, return mock validator IDs
        
        # Mock: Return 5 validator IDs (in production, query trust network)
        validator_ids = [user_id + i for i in range(1, min(pool_size, 5) + 1)]
        
        activity.logger.info(
            f"Selected {len(validator_ids)} validators for user {user_id}"
        )
        
        return validator_ids


@activity.defn
async def aggregate_validation_scores(
    approvals: list[dict[str, Any]], rejections: list[dict[str, Any]]
) -> float:
    """Aggregate community validation scores into confidence score.
    
    Weights validator responses by their reputation and trust score.
    Higher reputation validators have more weight in final confidence.
    
    Args:
        approvals: List of approval responses with validator metadata
        rejections: List of rejection responses with validator metadata
        
    Returns:
        Confidence score 0-100
    """
    activity.logger.info(
        f"Aggregating validation scores: {len(approvals)} approvals, "
        f"{len(rejections)} rejections"
    )
    
    if not approvals and not rejections:
        return 0.0
    
    # Simple aggregation: percentage of approvals
    # TODO: Implement reputation-weighted scoring
    total = len(approvals) + len(rejections)
    approval_pct = (len(approvals) / total) * 100
    
    # Apply confidence adjustment based on number of responses
    if total < 3:
        confidence_multiplier = 0.7  # Lower confidence with few validators
    elif total < 5:
        confidence_multiplier = 0.85
    else:
        confidence_multiplier = 1.0
    
    confidence_score = approval_pct * confidence_multiplier
    
    activity.logger.info(f"Confidence score: {confidence_score:.1f}")
    
    return confidence_score


@activity.defn
async def find_available_verifiers(
    location: str, time_slots: list[str], requirements: dict[str, Any]
) -> list[dict[str, Any]]:
    """Find available in-person verifiers matching requirements.
    
    Searches for authorized verifiers near the specified location
    with availability in the requested time slots.
    
    Args:
        location: Preferred verification location
        time_slots: List of preferred times (ISO format)
        requirements: Verifier requirements (certification, experience, etc.)
        
    Returns:
        List of available verifiers with metadata
    """
    activity.logger.info(
        f"Finding verifiers near {location}, {len(time_slots)} time slots"
    )
    
    # TODO: Implement geospatial query with PostGIS
    # For now, return mock verifiers
    
    verifiers = [
        {
            "verifier_id": 1001,
            "name": "Sarah Verifier",
            "location": location,
            "available_slots": time_slots[:2],
            "certifications": ["government_id", "notary"],
            "verifications_completed": 150,
            "rating": 4.8,
        },
        {
            "verifier_id": 1002,
            "name": "Mike Validator",
            "location": location,
            "available_slots": time_slots[1:],
            "certifications": ["government_id"],
            "verifications_completed": 75,
            "rating": 4.6,
        },
    ]
    
    activity.logger.info(f"Found {len(verifiers)} available verifiers")
    
    return verifiers


@activity.defn
async def schedule_verification_appointment(
    user_id: int, verifier: dict[str, Any], scheduled_time: str
) -> dict[str, Any]:
    """Schedule in-person verification appointment.
    
    Creates appointment record and sends notifications to both
    user and verifier.
    
    Args:
        user_id: User ID
        verifier: Verifier details
        scheduled_time: Appointment time (ISO format)
        
    Returns:
        Appointment details
    """
    activity.logger.info(
        f"Scheduling verification for user {user_id} with verifier "
        f"{verifier['verifier_id']} at {scheduled_time}"
    )
    
    # TODO: Create appointment in database
    # TODO: Send notifications
    
    appointment = {
        "appointment_id": f"apt-{user_id}-{verifier['verifier_id']}",
        "user_id": user_id,
        "verifier_id": verifier["verifier_id"],
        "scheduled_time": scheduled_time,
        "location": verifier["location"],
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    activity.logger.info(
        f"Scheduled appointment {appointment['appointment_id']}"
    )
    
    return appointment
