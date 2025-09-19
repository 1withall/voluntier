"""Authentication and user management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from voluntier.dependencies import (
    get_current_user, require_admin, create_token_pair, verify_refresh_token
)
from voluntier.database import get_db_session
from voluntier.models import User
from voluntier.services.validation_service import UserProfileUpdate

# Auth routes
auth_router = APIRouter()

@auth_router.post("/login")
async def login():
    """Login endpoint - requires implementation."""
    # This should be implemented with proper authentication logic
    return {"message": "Login endpoint - to be implemented"}

@auth_router.post("/register")
async def register():
    """Register endpoint - requires implementation."""
    # This should be implemented with proper registration logic
    return {"message": "Register endpoint - to be implemented"}

@auth_router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Refresh access token using refresh token."""
    try:
        user_id = verify_refresh_token(refresh_token)

        # Verify user still exists and is active
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new token pair
        access_token, new_refresh_token = create_token_pair(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# Users routes
users_router = APIRouter()

@users_router.get("/profile", response_model=dict)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get current user profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "phone": current_user.phone,
        "location": current_user.location,
        "timezone": current_user.timezone,
        "skills": current_user.skills,
        "interests": current_user.interests,
        "verification_status": current_user.verification_status.value if hasattr(current_user.verification_status, 'value') else str(current_user.verification_status),
        "trust_score": current_user.trust_score,
        "hours_logged": current_user.hours_logged,
        "events_attended": current_user.events_attended,
        "events_organized": current_user.events_organized,
        "is_active": current_user.is_active
    }

@users_router.put("/profile", response_model=dict)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user profile with validation."""
    # Update user profile
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()

    return {"message": "Profile updated successfully", "user_id": str(current_user.id)}


# Events routes
events_router = APIRouter()

@events_router.get("/", response_model=list)
async def list_events(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """List events accessible to current user."""
    # This should be implemented with proper event listing logic
    return {"message": "List events endpoint - to be implemented"}


# Organizations routes
organizations_router = APIRouter()

@organizations_router.get("/", response_model=list)
async def list_organizations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """List organizations accessible to current user."""
    # This should be implemented with proper organization listing logic
    return {"message": "List organizations endpoint - to be implemented"}


# Notifications routes
notifications_router = APIRouter()

@notifications_router.get("/", response_model=list)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """List notifications for current user."""
    # This should be implemented with proper notification listing logic
    return {"message": "List notifications endpoint - to be implemented"}