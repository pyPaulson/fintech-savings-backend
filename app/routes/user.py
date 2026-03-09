import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserResponse
from app.controllers.user import create_user
from app.database.session import get_db

router = APIRouter(prefix="/users", tags=["Users Endpoint"])
logger = logging.getLogger(__name__)


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
