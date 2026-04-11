import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import get_current_user
from app.controllers.account import get_account, get_user_accounts
from app.database.session import get_db
from app.models.user import User
from app.schemas.account import AccountResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])
logger = logging.getLogger(__name__)


async def _current_user_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(request, db)


def _ensure_admin_or_owner(current_user: User, account_user_id: UUID):
    if current_user.is_admin or current_user.id == account_user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this account",
    )


@router.get("/", response_model=list[AccountResponse])
async def list_my_accounts(
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    List accounts for the authenticated user.
    """
    try:
        return await get_user_accounts(current_user.id, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in list_my_accounts")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch accounts",
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account_by_id(
    account_id: UUID,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single account. Admins can view any; users can view their own.
    """
    try:
        account = await get_account(account_id, db)
        _ensure_admin_or_owner(current_user, account.user_id)
        return account
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in get_account_by_id")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account",
        )
