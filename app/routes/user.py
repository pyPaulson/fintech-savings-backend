import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import get_current_user
from app.controllers.user import (
    create_user,
    deactivate_user,
    update_user_profile,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger(__name__)


async def _current_user_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(request, db)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        return await create_user(user, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in register_user route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(_current_user_dependency),
):
    """
    Return info about the authenticated user.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    updates: UserUpdate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Update profile fields for the authenticated user.
    """
    try:
        return await update_user_profile(current_user, updates, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in update_current_user route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate the authenticated user's account.
    """
    try:
        await deactivate_user(current_user, db)
        return {"message": "Account deactivated"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in delete_current_user route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account",
        )
