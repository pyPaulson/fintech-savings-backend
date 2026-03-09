import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import get_current_user, login_user
from app.database.session import get_db
from app.schemas.user import UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/login")
async def login(
    user: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
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
