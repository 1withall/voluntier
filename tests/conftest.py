"""Pytest configuration and fixtures for testing.

Provides:
- Database fixtures with transaction rollback
- Test client for API endpoint testing
- Authentication fixtures for protected routes
"""
import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import Base, get_db
from app.models import User
from main import app


# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session.

    Returns:
        asyncio.AbstractEventLoop: Event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine.

    Uses test database and NullPool for transaction isolation.

    Yields:
        AsyncEngine: Database engine for tests.
    """
    # Use test database URL from settings
    engine = create_async_engine(
        settings.database_test_url,
        echo=False,
        poolclass=NullPool,  # Disable pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with transaction rollback.

    All database changes are rolled back after each test.

    Args:
        test_engine: Test database engine.

    Yields:
        AsyncSession: Database session for tests.
    """
    # Create session factory
    async_session_factory = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def test_client(test_db_session: AsyncSession) -> TestClient:
    """Create test client with database session override.

    Args:
        test_db_session: Test database session.

    Returns:
        TestClient: FastAPI test client.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """Create a test user.

    Args:
        test_db_session: Test database session.

    Returns:
        User: Created test user.
    """
    from app.core.security import hash_password

    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_verified=False,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def verified_test_user(test_db_session: AsyncSession) -> User:
    """Create a verified test user.

    Args:
        test_db_session: Test database session.

    Returns:
        User: Created verified test user.
    """
    from app.core.security import hash_password

    user = User(
        email="verified@example.com",
        hashed_password=hash_password("VerifiedPassword123!"),
        full_name="Verified User",
        is_active=True,
        is_verified=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for test user.

    Args:
        test_user: Test user to create token for.

    Returns:
        dict: Authorization headers with Bearer token.
    """
    from app.core.security import create_access_token

    token = create_access_token({"sub": test_user.email})

    return {"Authorization": f"Bearer {token}"}
