"""Pydantic schemas for authentication endpoints.

This module defines request and response models for:
- User registration
- Login (token generation)
- Token refresh
- User responses
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    """User registration request schema.

    Attributes:
        email: Valid email address (unique).
        password: Password (min 8 characters).
        full_name: User's full name.

    Example:
        >>> user_data = UserRegister(
        ...     email="volunteer@example.com",
        ...     password="SecurePass123!",
        ...     full_name="Jane Smith"
        ... )
    """

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    full_name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "volunteer@example.com",
                "password": "SecurePass123!",
                "full_name": "Jane Smith",
            }
        }
    )


class UserLogin(BaseModel):
    """User login request schema (OAuth2 password flow).

    Attributes:
        username: Email address (called username for OAuth2 compatibility).
        password: User's password.

    Example:
        >>> login_data = UserLogin(
        ...     username="volunteer@example.com",
        ...     password="SecurePass123!"
        ... )
    """

    username: EmailStr  # OAuth2 spec requires "username" field
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "volunteer@example.com",
                "password": "SecurePass123!",
            }
        }
    )


class Token(BaseModel):
    """JWT token response schema.

    Attributes:
        access_token: JWT access token (short-lived, 30 min).
        refresh_token: JWT refresh token (long-lived, 7 days).
        token_type: Token type (always "bearer").

    Example:
        >>> token_response = Token(
        ...     access_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     refresh_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
        ...     token_type="bearer"
        ... )
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
            }
        }
    )


class TokenRefresh(BaseModel):
    """Token refresh request schema.

    Attributes:
        refresh_token: The refresh token to exchange for new tokens.

    Example:
        >>> refresh_request = TokenRefresh(
        ...     refresh_token="eyJ0eXAiOiJKV1QiLCJhbGc..."
        ... )
    """

    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        }
    )


class UserResponse(BaseModel):
    """User response schema (public user data).

    Attributes:
        id: User's unique ID.
        email: User's email address.
        full_name: User's full name.
        is_active: Account active status.
        is_verified: Email verification status.
        verification_status: Identity verification status.
        reputation_score: User's reputation score (0-100).

    Example:
        >>> user = UserResponse(
        ...     id=1,
        ...     email="volunteer@example.com",
        ...     full_name="Jane Smith",
        ...     is_active=True,
        ...     is_verified=True,
        ...     verification_status="verified",
        ...     reputation_score=85.5
        ... )
    """

    id: int
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    verification_status: str
    reputation_score: float

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "volunteer@example.com",
                "full_name": "Jane Smith",
                "is_active": True,
                "is_verified": True,
                "verification_status": "verified",
                "reputation_score": 85.5,
            }
        },
    )


class UserRegisterResponse(BaseModel):
    """User registration success response.

    Attributes:
        user: The created user's public data.
        message: Success message.

    Example:
        >>> response = UserRegisterResponse(
        ...     user=UserResponse(...),
        ...     message="Registration successful. Please verify your email."
        ... )
    """

    user: UserResponse
    message: str = "Registration successful. Please verify your email."

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": 1,
                    "email": "volunteer@example.com",
                    "full_name": "Jane Smith",
                    "is_active": True,
                    "is_verified": False,
                    "verification_status": "pending",
                    "reputation_score": 0.0,
                },
                "message": "Registration successful. Please verify your email.",
            }
        }
    )
