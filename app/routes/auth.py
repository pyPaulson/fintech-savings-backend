import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.google_auth import oauth


from app.controllers.auth import (
    confirm_email_verification,
    get_current_user,
    login_user,
    request_email_verification,
    request_password_reset,
    reset_password,
)
from app.controllers.google_auth import handle_google_user
from app.database.session import get_db
from app.core.config import settings
from app.utils.rate_limit import check_rate_limit
from app.schemas.user import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
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
    """
    Log in user
    """ 
    try:
        return await login_user(user, db, response)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/forgot-password")
async def forgot_password(
    payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    """
    Initiate password reset (token returned for dev/testing; email in production).
    """
    try:
        return await request_password_reset(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during forgot password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start password reset",
        )


@router.post("/reset-password")
async def reset_password_endpoint(
    payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Complete password reset with a valid token.
    """
    try:
        return await reset_password(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during password reset")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.post("/request-email-verification")
async def request_email_verification_endpoint(
    payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """
    Ask for an email verification token.
    """
    try:
        return await request_email_verification(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during email verification request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to request verification",
        )


@router.post("/verify-email")
async def verify_email(
    payload: EmailVerificationConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Confirm email address with verification token.
    """
    try:
        return await confirm_email_verification(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during email verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.get("/me", response_model=UserResponse)
async def current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get the current logged in user.
    """   
    try:
        return await get_current_user(request, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during current user lookup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current user",
        )


@router.get("/google/login")
async def google_login(request: Request):
    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception:
        logger.exception("Unhandled error during Google login redirect")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to initiate Google login",
        )


@router.get("/google/callback")
async def google_callback(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Google user information",
            )

        _, jwt_token = await handle_google_user(user_info, db)

        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {"message": "Google login successful"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during Google login callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google login failed",
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )
