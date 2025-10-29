def main():
    """Voluntier FastAPI application entry point.

    This module initializes and configures the FastAPI application with:
    - Database connection management
    - API routers and endpoints
    - CORS middleware
    - Error handling
    """


from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api import v1_router
from app.api.v1.auth import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connections
    - Shutdown: Close database connections and cleanup

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control to the application after startup.
    """
    # Startup
    await init_db()
    print(f"✓ Database initialized ({settings.environment})")

    yield

    # Shutdown
    await close_db()
    print("✓ Database connections closed")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Community volunteer connection platform",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure SlowAPI rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Simple message confirming API is running.
    """
    return {
        "message": "Voluntier API is running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Detailed health check with database status.

    Returns:
        dict: Health status of the application and its dependencies.

    TODO: Add database ping to verify connection.
    """
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Implement actual DB ping
    }


# Include API routers
app.include_router(v1_router, prefix="/api")


if __name__ == "__main__":
    main()
