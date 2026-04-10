"""
Auth route aggregator. Keeps /auth paths stable while grouping session, password,
verification, and Google OAuth flows into dedicated routers.
"""

from fastapi import APIRouter

from app.routes.auth_session import router as session_router
from app.routes.auth_password import router as password_router
from app.routes.auth_verification import router as verification_router
from app.routes.auth_google import router as google_router

router = APIRouter()
router.include_router(session_router)
router.include_router(password_router)
router.include_router(verification_router)
router.include_router(google_router)
