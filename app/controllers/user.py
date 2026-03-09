from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
import logging
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


async def create_user(user: UserCreate, db: AsyncSession) -> User:
    try:
        result = await db.execute(select(User).where(User.email == user.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        try:
            password_hash = hash_password(user.password)
        except Exception:
            logger.exception("Password hashing failed during user creation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process password",
            )

        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=password_hash,
            phone_number=user.phone_number,
            gender=user.gender,
            date_of_birth=user.date_of_birth,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        error_text = str(exc.orig).lower() if exc.orig else ""
        if "email" in error_text:
            detail = "Email already registered"
        elif "phone_number" in error_text or "phone" in error_text:
            detail = "Phone number already registered"
        else:
            detail = "A unique field already exists"

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while creating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating user",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while creating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating user",
        )
