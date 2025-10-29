"""Authentication API endpoints.

This module provides:
- POST /register: User registration
- POST /login: User authentication (token generation)
- POST /refresh: Token refresh

All endpoints rate limited to 10 requests/minute per PRD §4.3.1.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.database import get_db
from app.models import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserRegisterResponse,
    UserResponse,
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["authentication"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserRegisterResponse:
    """Register a new user account.

    Creates a new user with hashed password and default verification status.
    Email must be unique across the system.

    Args:
        user_data: User registration data (email, password, full_name).
        db: Database session (injected).

    Returns:
        Created user's public data and success message.

    Raises:
        HTTPException 400: Email already registered.

    Example:
        >>> POST /api/v1/auth/register
        >>> {
        ...     "email": "volunteer@example.com",
        ...     "password": "SecurePass123!",
        ...     "full_name": "Jane Smith"
        ... }
        >>> Response 201: {
        ...     "user": {...},
        ...     "message": "Registration successful. Please verify your email."
        ... }
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
        verification_status="pending",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserRegisterResponse(
        user=UserResponse.model_validate(new_user),
        message="Registration successful. Please verify your email.",
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: UserLogin = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate user and generate JWT tokens.

    Validates credentials and returns access and refresh tokens.
    Implements OAuth2 password flow.

    Args:
        credentials: Login credentials (username=email, password).
        db: Database session (injected).

    Returns:
        Access and refresh JWT tokens.

    Raises:
        HTTPException 401: Invalid credentials or inactive account.

    Example:
        >>> POST /api/v1/auth/login
        >>> {
        ...     "username": "volunteer@example.com",
        ...     "password": "SecurePass123!"
        ... }
        >>> Response 200: {
        ...     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     "token_type": "bearer"
        ... }
    """
    # Find user by email (username field for OAuth2 compatibility)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Refresh access and refresh tokens.

    Exchanges a valid refresh token for new access and refresh tokens.
    Old refresh token is invalidated (stateless, relies on expiration).

    Args:
        token_data: Refresh token to exchange.
        db: Database session (injected).

    Returns:
        New access and refresh JWT tokens.

    Raises:
        HTTPException 401: Invalid or expired refresh token.
        HTTPException 401: User not found or inactive.

    Example:
        >>> POST /api/v1/auth/refresh
        >>> {
        ...     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        ... }
        >>> Response 200: {
        ...     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     "token_type": "bearer"
        ... }
    """
    try:
        # Decode and validate refresh token
        payload = decode_token(token_data.refresh_token)

        # Verify it's a refresh token
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload.get("sub")
        if not email or not isinstance(email, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )
