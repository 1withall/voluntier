"""Security utilities for authentication and authorization.

This module provides:
- Password hashing with bcrypt
- JWT token generation and validation
- OAuth2 password bearer scheme
- Token refresh logic
- Current user dependency for protected endpoints
"""

from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password from database.

    Returns:
        True if password matches, False otherwise.

    Example:
        >>> hashed = hash_password("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Bcrypt hashed password string.

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token (typically {"sub": user_id}).
        expires_delta: Optional custom expiration time. Defaults to settings.access_token_expire_minutes.

    Returns:
        Encoded JWT token string.

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> # Token valid for 30 minutes (default from settings)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration.

    Args:
        data: Dictionary of claims to encode (typically {"sub": user_id}).

    Returns:
        Encoded JWT refresh token string.

    Example:
        >>> token = create_refresh_token({"sub": "user@example.com"})
        >>> # Token valid for 7 days (default from settings)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        Dictionary of decoded claims.

    Raises:
        JWTError: If token is invalid, expired, or malformed.

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user@example.com'
        >>> payload["type"]
        'access'
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e


def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    """Verify that a decoded token payload has the expected type.

    Args:
        payload: Decoded JWT token payload.
        expected_type: Expected token type ("access" or "refresh").

    Returns:
        True if token type matches, False otherwise.

    Example:
        >>> access_token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_token(access_token)
        >>> verify_token_type(payload, "access")
        True
        >>> verify_token_type(payload, "refresh")
        False
    """
    return payload.get("type") == expected_type


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(),
) -> Any:  # Returns User model
    """FastAPI dependency to get the current authenticated user.

    Extracts and validates JWT token from Authorization header,
    then retrieves the corresponding user from the database.

    Args:
        token: JWT token from Authorization header.
        db: Database session (injected).

    Returns:
        User model instance of authenticated user.

    Raises:
        HTTPException 401: Invalid token, expired token, or user not found.

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> from app.models import User
        >>>
        >>> router = APIRouter()
        >>>
        >>> @router.get("/me")
        >>> async def get_me(user: User = Depends(get_current_user)):
        ...     return {"email": user.email}
    """
    from app.database import get_db  # Import here to avoid circular dependency
    from app.models import User  # Import here to avoid circular dependency

    # Get database session
    if db is None:
        async for session in get_db():
            db = session
            break

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = decode_token(token)

        # Verify it's an access token
        if not verify_token_type(payload, "access"):
            raise credentials_exception

        # Extract email
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user
