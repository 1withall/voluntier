"""Local activities for fast, in-process execution.

Local activities execute directly in the worker process without going through
the Temporal task queue. They are ideal for:
- Simple database reads (< 1 second)
- Cached data lookups
- Local computations

Characteristics:
- Execute in-process (no network overhead)
- Fast execution (< 1 second recommended)
- Limited retry capabilities (fail fast)
- Lower latency than regular activities

Based on Temporal Python SDK best practices from Context7.
"""

from temporalio import activity

from app.database import get_session_factory
from app.models import User


def _get_session():
    """Helper to get database session for local activities."""
    return get_session_factory()()


@activity.defn
async def get_user_reputation_local(user_id: int) -> float:
    """Get user reputation score with local activity (fast, in-process).

    This is a local activity optimized for speed. It should complete in < 1 second.
    Used when workflows need quick reputation lookups without full activity overhead.

    Args:
        user_id: User ID to fetch reputation for.

    Returns:
        float: User reputation score (0-100), or 0.0 if user not found.

    Example:
        >>> # In workflow:
        >>> reputation = await workflow.execute_local_activity(
        ...     get_user_reputation_local,
        ...     user_id,
        ...     schedule_to_close_timeout=timedelta(seconds=1)
        ... )
    """
    async with _get_session() as session:
        user = await session.get(User, user_id)
        return user.reputation_score if user else 0.0


@activity.defn
async def get_user_verification_score_local(user_id: int) -> float:
    """Get user verification score with local activity (fast, in-process).

    Local activity for quick verification score lookups without activity queue overhead.

    Args:
        user_id: User ID to fetch verification score for.

    Returns:
        float: User verification score (0-100), or 0.0 if user not found.

    Example:
        >>> # In workflow:
        >>> score = await workflow.execute_local_activity(
        ...     get_user_verification_score_local,
        ...     user_id,
        ...     schedule_to_close_timeout=timedelta(seconds=1)
        ... )
    """
    async with _get_session() as session:
        user = await session.get(User, user_id)
        return user.verification_score if user else 0.0


@activity.defn
async def check_user_exists_local(user_id: int) -> bool:
    """Check if user exists with local activity (fast, in-process).

    Local activity for quick user existence checks.

    Args:
        user_id: User ID to check.

    Returns:
        bool: True if user exists, False otherwise.

    Example:
        >>> # In workflow:
        >>> exists = await workflow.execute_local_activity(
        ...     check_user_exists_local,
        ...     user_id,
        ...     schedule_to_close_timeout=timedelta(seconds=1)
        ... )
    """
    async with _get_session() as session:
        user = await session.get(User, user_id)
        return user is not None


@activity.defn
async def get_user_email_local(user_id: int) -> str | None:
    """Get user email with local activity (fast, in-process).

    Local activity for quick email lookups.

    Args:
        user_id: User ID to fetch email for.

    Returns:
        str | None: User email if exists, None otherwise.

    Example:
        >>> # In workflow:
        >>> email = await workflow.execute_local_activity(
        ...     get_user_email_local,
        ...     user_id,
        ...     schedule_to_close_timeout=timedelta(seconds=1)
        ... )
    """
    async with _get_session() as session:
        user = await session.get(User, user_id)
        return user.email if user else None
