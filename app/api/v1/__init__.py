"""API v1 router aggregation.

This module combines all v1 API endpoints into a single router.
"""

from fastapi import APIRouter

from app.api.v1 import auth, verification

router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(auth.router)
router.include_router(verification.router)

# Future routers will be added here:
# router.include_router(users.router)
# router.include_router(opportunities.router)
# router.include_router(matches.router)
