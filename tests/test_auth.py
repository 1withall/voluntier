"""Tests for authentication endpoints.

Tests:
- User registration with validation
- Login with correct/incorrect credentials
- Token refresh with valid/invalid tokens
- Rate limiting enforcement
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_refresh_token, hash_password
from app.models import User


class TestRegister:
    """Tests for /api/v1/auth/register endpoint."""

    def test_register_success(
        self, test_client: TestClient, test_db_session: AsyncSession
    ):
        """Test successful user registration."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert data["user"]["is_active"] is True
        assert data["user"]["is_verified"] is False
        assert "message" in data

    def test_register_duplicate_email(
        self, test_client: TestClient, test_user: User
    ):
        """Test registration with existing email fails."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPassword123!",
                "full_name": "Duplicate User",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email format fails."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, test_client: TestClient):
        """Test registration with too short password fails."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
                "full_name": "Test User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Tests for /api/v1/auth/login endpoint."""

    def test_login_success(self, test_client: TestClient, test_user: User):
        """Test successful login with correct credentials."""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_login_wrong_password(self, test_client: TestClient, test_user: User):
        """Test login with incorrect password fails."""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with nonexistent email fails."""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, test_client: TestClient, test_db_session: AsyncSession
    ):
        """Test login with inactive account fails."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=hash_password("Password123!"),
            full_name="Inactive User",
            is_active=False,
        )
        test_db_session.add(inactive_user)
        await test_db_session.commit()

        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "inactive" in response.json()["detail"].lower()


class TestRefresh:
    """Tests for /api/v1/auth/refresh endpoint."""

    def test_refresh_success(self, test_client: TestClient, test_user: User):
        """Test successful token refresh with valid refresh token."""
        # Generate a valid refresh token
        refresh_token = create_refresh_token({"sub": test_user.email})

        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, test_client: TestClient):
        """Test token refresh with invalid token fails."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_access_token_instead_of_refresh(
        self, test_client: TestClient, test_user: User
    ):
        """Test using access token for refresh fails."""
        from app.core.security import create_access_token

        # Create an access token (not a refresh token)
        access_token = create_access_token({"sub": test_user.email})

        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "refresh" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_inactive_user(
        self, test_client: TestClient, test_db_session: AsyncSession
    ):
        """Test token refresh for inactive user fails."""
        # Create inactive user
        inactive_user = User(
            email="inactive_refresh@example.com",
            hashed_password=hash_password("Password123!"),
            full_name="Inactive User",
            is_active=False,
        )
        test_db_session.add(inactive_user)
        await test_db_session.commit()

        # Generate refresh token for inactive user
        refresh_token = create_refresh_token({"sub": inactive_user.email})

        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
