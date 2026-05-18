import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.google_auth import handle_google_user, login_with_google_token
from app.core.config import settings
from app.database.session import get_db
from app.schemas.user import AuthSessionResponse, GoogleTokenLoginRequest
from app.utils.google_auth import oauth

router = APIRouter(prefix="/auth/google", tags=["Auth • Google"])
logger = logging.getLogger(__name__)


@router.get("/login")
async def google_login(request: Request):
    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception:
        logger.exception("Unhandled error during Google login redirect")
        raise HTTPException(
            status_code=500,
            detail="Unable to initiate Google login",
        )


@router.get("/callback")
async def google_callback(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=400,
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
            status_code=500,
            detail="Google login failed",
        )


@router.post("/mobile", response_model=AuthSessionResponse)
async def google_mobile_login(
    payload: GoogleTokenLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login_with_google_token(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during mobile Google login")
        raise HTTPException(
            status_code=500,
            detail="Google login failed",
        )
