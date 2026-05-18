import logging
import secrets

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.services.account_service import create_default_accounts
from app.models.user import User
from app.schemas.user import AuthSessionResponse, GoogleTokenLoginRequest, UserResponse
from app.utils.google_tokens import verify_google_identity_token
from app.utils.jwt import create_access_token
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


async def handle_google_user(user_info: dict, db: AsyncSession):
    email = user_info.get("email")
    google_id = user_info.get("sub")
    first_name = user_info.get("given_name")
    last_name = user_info.get("family_name")
    picture = user_info.get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email",
        )

    email = email.strip().lower()

    try:
        result = await db.execute(select(User).where(func.lower(User.email) == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            user = existing_user
        else:
            try:
                password_hash = hash_password(secrets.token_urlsafe(32))
            except Exception:
                logger.exception("Password hashing failed for new Google user")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to secure Google account",
                )

            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                auth_provider="google",
                profile_picture=picture,
                is_verified=True,
                password_hash=password_hash,
            )

            db.add(user)
            await db.flush()
            await create_default_accounts(user.id, db)
            await db.commit()
            await db.refresh(user)

        if existing_user:
            changed = False
            if google_id and not user.google_id:
                user.google_id = google_id
                changed = True
            if picture and user.profile_picture != picture:
                user.profile_picture = picture
                changed = True
            if not user.is_verified:
                user.is_verified = True
                changed = True
            if not user.auth_provider:
                user.auth_provider = "google"
                changed = True
            if changed:
                db.add(user)
                await db.commit()
                await db.refresh(user)

        token = create_access_token({"user_id": user.id})
        return user, token

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        logger.exception("Unique constraint failed while syncing Google user")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Google account is already linked to another user",
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while syncing Google user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process Google account",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while syncing Google user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed",
        )


async def login_with_google_token(payload: GoogleTokenLoginRequest, db: AsyncSession):
    try:
        user_info = verify_google_identity_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user, token = await handle_google_user(user_info, db)
    user_payload = UserResponse.model_validate(user)
    return AuthSessionResponse(
        message="Google login successful",
        access_token=token,
        user=user_payload,
    ).model_dump()
