import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.admin import admins_exist, create_admin, list_users
from app.controllers.auth import get_current_user
from app.controllers.user import (
    deactivate_user,
    get_user_by_id,
    update_user_profile,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users/admin", tags=["Admin Users"])
logger = logging.getLogger(__name__)


async def _current_user_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(request, db)


def _ensure_admin(user: User):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@router.get("/", response_model=list[UserResponse])
async def list_all_users(
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only list of every user.
    """
    _ensure_admin(current_user)
    try:
        return await list_users(db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in list_all_users route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users",
        )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_admin(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new admin account (admin only).
    """
    try:
        has_admin = await admins_exist(db)
        current_user: User | None = None

        if has_admin:
            try:
                current_user = await get_current_user(request, db)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            _ensure_admin(current_user)

        return await create_admin(user, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in register_admin route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register admin",
        )


@router.patch("/me", response_model=UserResponse)
async def update_current_admin(
    updates: UserUpdate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Update profile fields for the authenticated admin (admin only).
    """
    _ensure_admin(current_user)
    try:
        return await update_user_profile(current_user, updates, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in update_current_admin route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin profile",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: UUID,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a specific user by ID (admin only).
    """
    _ensure_admin(current_user)

    try:
        return await get_user_by_id(user_id, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in read_user_by_id route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user",
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: UUID,
    updates: UserUpdate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Modify a user’s profile (admin only).
    """
    _ensure_admin(current_user)
    try:
        target_user = await get_user_by_id(user_id, db)
        return await update_user_profile(target_user, updates, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in update_user_by_admin route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/{user_id}")
async def deactivate_user_by_admin(
    user_id: UUID,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user account (admin only).
    """
    _ensure_admin(current_user)
    try:
        target_user = await get_user_by_id(user_id, db)
        await deactivate_user(target_user, db)
        return {"message": "Account deactivated"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in deactivate_user_by_admin route")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user",
        )
