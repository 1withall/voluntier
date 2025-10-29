"""API package initialization.

This package contains all API endpoints organized by version.
"""

from app.api.v1 import router as v1_router

__all__ = ["v1_router"]
