"""
Database connection and session management.

This module provides:
- Async SQLAlchemy engine creation
- AsyncSession factory with proper configuration
- Dependency injection for FastAPI routes
- PostGIS support for geospatial queries
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends

from app.config import settings


# Declarative Base for all ORM models
class Base(DeclarativeBase):
    """Base class for all database models.
    
    All models should inherit from this class to be tracked
    by SQLAlchemy's metadata system and support Alembic migrations.
    """
    pass


# Global engine instance (initialized at startup)
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine.
    
    Returns:
        AsyncEngine: The singleton database engine instance.
        
    Raises:
        RuntimeError: If engine hasn't been initialized yet.
        
    Example:
        >>> engine = get_engine()
        >>> async with engine.begin() as conn:
        ...     await conn.execute(text("SELECT 1"))
    """
    global _engine
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. Call init_db() at startup."
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the async session factory.
    
    Returns:
        async_sessionmaker: Factory for creating AsyncSession instances.
        
    Raises:
        RuntimeError: If session factory hasn't been initialized.
        
    Example:
        >>> SessionLocal = get_session_factory()
        >>> async with SessionLocal() as session:
        ...     result = await session.execute(select(User))
    """
    global _async_session_factory
    if _async_session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_db() at startup."
        )
    return _async_session_factory


async def init_db() -> None:
    """Initialize database connection and session factory.
    
    This should be called once at application startup. Creates:
    - Async engine with asyncpg driver
    - Session factory with expire_on_commit=False
    - PostGIS extension enablement (if needed)
    
    Example:
        >>> # In main.py startup event
        >>> @app.on_event("startup")
        >>> async def startup():
        ...     await init_db()
    """
    global _engine, _async_session_factory
    
    # Create async engine with asyncpg driver
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,  # Log SQL statements in debug mode
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    
    # Create session factory with optimized settings
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
        autoflush=False,  # Explicit flush control for better performance
    )
    
    # Enable PostGIS extension if not already enabled
    # This is idempotent and safe to run multiple times
    async with _engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))


async def close_db() -> None:
    """Close database connections and cleanup resources.
    
    This should be called once at application shutdown.
    Properly disposes of the engine and all connection pools.
    
    Example:
        >>> # In main.py shutdown event
        >>> @app.on_event("shutdown")
        >>> async def shutdown():
        ...     await close_db()
    """
    global _engine, _async_session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    
    _async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.
    
    Provides a transactional AsyncSession that automatically:
    - Opens a new session from the factory
    - Yields it to the route handler
    - Commits on success
    - Rolls back on exception
    - Closes the session when done
    
    Yields:
        AsyncSession: Database session for the request.
        
    Example:
        >>> from fastapi import APIRouter, Depends
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> 
        >>> router = APIRouter()
        >>> 
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(
        ...     user_id: int,
        ...     db: AsyncSession = Depends(get_db)
        ... ):
        ...     result = await db.execute(
        ...         select(User).where(User.id == user_id)
        ...     )
        ...     return result.scalar_one_or_none()
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for dependency injection
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
