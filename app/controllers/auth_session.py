from __future__ import annotations

import logging

from fastapi import HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserLogin
from app.utils.jwt import create_access_token, decode_access_token
from app.utils.security import verify_password

logger = logging.getLogger(__name__)


def _extract_token_from_request(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def login_user(user: UserLogin, db: AsyncSession, response: Response):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == user.email)
        )
        db_user = result.scalar_one_or_none()

        try:
            password_ok = db_user and verify_password(user.password, db_user.password_hash)
        except Exception:
            logger.exception("Password verification failed during login")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication process failed",
            )

        if not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        access_token = create_access_token({"user_id": db_user.id})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {"message": "Login successful"}

    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Database error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during login",
        )
    except Exception:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


async def get_current_user(request: Request, db: AsyncSession) -> User:
    token = _extract_token_from_request(request)

    try:
        payload = decode_access_token(token)
        user_id = payload["user_id"]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while resolving current user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while resolving current user",
        )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return db_user
