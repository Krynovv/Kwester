from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.redis import get_redis
from ..core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    get_user_id_by_refresh_token,
    revoke_refresh_token,
)
from ..models.user import User
from ..models.stat import Stat
from ..core.constant import DEFAULT_STATS
from ..schemas.user import UserCreate, UserRead, Token, RefreshRequest
from ..models.boss import Boss
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
      username=data.username,
      email=data.email,
      password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    for stat_data in DEFAULT_STATS:
        db.add(Stat(user_id=user.id, name=stat_data["name"], combat_role=stat_data["combat_role"], is_default=True,))
    
    db.add(Boss(user_id=user.id))

    await db.commit()
    await db.refresh(user)
    return user

@router.post("/token", response_model=Token)
async def login (
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token()
    await store_refresh_token(redis, refresh_token, user.id)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh(
    data: RefreshRequest,
    redis: Redis = Depends(get_redis),
):
    user_id = await get_user_id_by_refresh_token(redis, data.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Rotate: revoke the used refresh token and issue a new one.
    await revoke_refresh_token(redis, data.refresh_token)
    new_refresh_token = create_refresh_token()
    await store_refresh_token(redis, new_refresh_token, int(user_id))

    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    redis: Redis = Depends(get_redis),
):
    await revoke_refresh_token(redis, data.refresh_token)

