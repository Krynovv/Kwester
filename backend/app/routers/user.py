from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.database import get_db
from ..models.user import User
from ..schemas.user import UserRead

router = APIRouter(prefix = "/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

