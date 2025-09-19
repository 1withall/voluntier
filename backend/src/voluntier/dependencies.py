"""
Authentication dependencies for FastAPI routes.
Provides dependency injection for user authentication and authorization.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db_session
from .models import User
from .config import get_settings

settings = get_settings()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.secret_key if hasattr(settings, 'secret_key') else os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Dependency to get the current authenticated user.
    Validates JWT token and returns user from database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user (alias for get_current_user)."""
    return current_user


def require_privilege(required_privilege: str):
    """
    Create a dependency that requires a specific privilege level.
    Usage: Depends(require_privilege("admin"))
    """
    async def privilege_checker(current_user: User = Depends(get_current_user)):
        # For now, implement basic role-based checking
        # This can be extended to support the full privilege system
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

        # Define privilege hierarchy
        privilege_levels = {
            "volunteer": 1,
            "organization": 2,
            "moderator": 3,
            "admin": 4
        }

        required_level = privilege_levels.get(required_privilege.lower(), 999)
        user_level = privilege_levels.get(user_role.lower(), 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required: {required_privilege}, User role: {user_role}"
            )

        return current_user

    return privilege_checker


# Specific privilege dependencies for common use cases
require_admin = require_privilege("admin")
require_moderator = require_privilege("moderator")
require_organization = require_privilege("organization")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns user if authenticated, None if not.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None