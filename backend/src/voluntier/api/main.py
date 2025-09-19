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
from voluntier.api.memory import router as memory_router
from voluntier.api.security import get_security_router
from voluntier.database import close_db_connections
from voluntier.middleware.logging import LoggingMiddleware
from voluntier.middleware.security import AdvancedSecurityMiddleware
from voluntier.middleware.metrics import MetricsMiddleware
from voluntier.services.security_service import security_service
from voluntier.services.threat_detection import threat_detection_system
from voluntier.services.honeypot_system import honeypot_manager
from voluntier.services.audit_service import audit_service
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
        # Initialize security services
        logger.info("Initializing security services...")
        await security_service.initialize()
        await threat_detection_system.initialize()
        await honeypot_manager.initialize()
        await audit_service.initialize()
        
        logger.info("Security services initialized successfully")
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voluntier API server")
    
    try:
        # Shutdown security services
        await security_service.shutdown()
        await audit_service.shutdown()
        
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
        description="Autonomous agent-driven volunteer coordination platform with advanced security",
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
    
    logger.info(f"Created FastAPI app for {settings.environment} environment with advanced security")
    
    return app


def add_middleware(app: FastAPI) -> None:
    """Add middleware to the FastAPI application."""
    
    # Advanced Security middleware (first for comprehensive security)
    app.add_middleware(AdvancedSecurityMiddleware)
    
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
    
    # Security API routes (high priority)
    app.include_router(
        get_security_router(),
        tags=["Security"],
    )
    
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
    
    app.include_router(
        memory_router,
        prefix=f"{settings.api_prefix}",
        tags=["Memory"],
    )
    
    # Health check endpoint with security status
    @app.get("/health")
    async def health_check():
        """Health check endpoint with security status."""
        security_status = "active" if security_service.security_active else "inactive"
        threat_detection_status = "active" if threat_detection_system.detection_active else "inactive"
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "security": {
                "security_service": security_status,
                "threat_detection": threat_detection_status,
                "honeypots_deployed": len(honeypot_manager.honeypots)
            }
        }
    
    # Security status endpoint
    @app.get("/security/status")
    async def security_status():
        """Security system status endpoint."""
        if not security_service.security_active:
            return JSONResponse(
                status_code=503,
                content={"status": "Security services not active"}
            )
            
        detection_stats = await threat_detection_system.get_detection_statistics()
        honeypot_stats = await honeypot_manager.get_honeypot_statistics()
        
        return {
            "security_active": security_service.security_active,
            "threat_detection": detection_stats,
            "honeypots": honeypot_stats,
            "last_updated": asyncio.get_event_loop().time()
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Voluntier API - Secure Volunteer Platform",
            "version": settings.app_version,
            "security": "Advanced threat detection and response enabled",
            "docs": "/docs" if settings.debug else "Contact admin for documentation",
        }


# Create the app instance
app = create_app()