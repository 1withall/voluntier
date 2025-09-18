"""FastAPI application main module."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from voluntier.config import settings
from voluntier.api.routes import (
    auth_router,
    users_router,
    events_router,
    organizations_router,
    notifications_router,
    temporal_router,
)
from voluntier.database import close_db_connections
from voluntier.middleware.logging import LoggingMiddleware
from voluntier.middleware.security import SecurityMiddleware
from voluntier.middleware.metrics import MetricsMiddleware
from voluntier.utils.logging import setup_logging
from voluntier.utils.exceptions import setup_exception_handlers

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Voluntier API server")
    
    # Initialize services
    try:
        # Here you would initialize any startup services
        # e.g., connect to external services, initialize caches, etc.
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voluntier API server")
    
    try:
        # Close database connections
        await close_db_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging first
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous agent-driven volunteer coordination platform",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    add_middleware(app)
    
    # Add routes
    add_routes(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    logger.info(f"Created FastAPI app for {settings.environment} environment")
    
    return app


def add_middleware(app: FastAPI) -> None:
    """Add middleware to the FastAPI application."""
    
    # Security middleware (first for security)
    app.add_middleware(SecurityMiddleware)
    
    # Trusted host middleware
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["voluntier.org", "*.voluntier.org"],
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Logging middleware (last for complete request logging)
    app.add_middleware(LoggingMiddleware)


def add_routes(app: FastAPI) -> None:
    """Add routes to the FastAPI application."""
    
    # API routes
    app.include_router(
        auth_router,
        prefix=f"{settings.api_prefix}/auth",
        tags=["Authentication"],
    )
    
    app.include_router(
        users_router,
        prefix=f"{settings.api_prefix}/users",
        tags=["Users"],
    )
    
    app.include_router(
        events_router,
        prefix=f"{settings.api_prefix}/events",
        tags=["Events"],
    )
    
    app.include_router(
        organizations_router,
        prefix=f"{settings.api_prefix}/organizations",
        tags=["Organizations"],
    )
    
    app.include_router(
        notifications_router,
        prefix=f"{settings.api_prefix}/notifications",
        tags=["Notifications"],
    )
    
    app.include_router(
        temporal_router,
        prefix=f"{settings.api_prefix}/workflows",
        tags=["Workflows"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Voluntier API",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "Contact admin for documentation",
        }


# Create the app instance
app = create_app()