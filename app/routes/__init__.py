from fastapi import APIRouter

# Create main router
router = APIRouter()

# Import all route modules
from .profiles import router as profiles_router
from .auth import router as auth_router
from .billing import router as billing_router

# Include routers
router.include_router(auth_router)

# Export all routers
__all__ = ["router", "profiles_router", "auth_router", "billing_router"] 