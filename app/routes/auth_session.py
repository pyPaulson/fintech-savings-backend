import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_session import get_current_user, login_user
from app.database.session import get_db
from app.core.config import settings
from app.schemas.user import UserLogin, UserResponse
from app.utils.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["Auth • Session"])
logger = logging.getLogger(__name__)


async def _rate_limit_login(request: Request):
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else None) or (
        request.client.host if request.client else "unknown"
    )
    await check_rate_limit(
        "login",
        client_ip,
        limit=settings.RATE_LIMIT_LOGIN_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )


@router.post("/login")
async def login(
    user: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_rate_limit_login),
):
    """Log in a user and issue a JWT cookie."""
    try:
        return await login_user(user, db, response)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during login")
        raise HTTPException(
            status_code=500,
            detail="Login failed",
        )


@router.get("/me", response_model=UserResponse)
async def current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Get the currently authenticated user."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during current user lookup")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch current user",
        )


@router.post("/logout")
async def logout(response: Response):
    """Clear the authentication cookie to log the user out."""
    try:
        response.delete_cookie("access_token")
        return {"message": "Logout successful"}
    except Exception:
        logger.exception("Unhandled error during logout")
        raise HTTPException(
            status_code=500,
            detail="Logout failed",
        )
