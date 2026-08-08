from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select

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
from ..core.ratelimit import (
    LOGIN_FAILURE_LIMIT,
    LOGIN_FAILURE_WINDOW,
    REGISTER_RATE_LIMIT,
    REGISTER_RATE_WINDOW,
    check_rate_limit,
    client_ip,
    enforce_rate_limit,
    record_attempt,
    reset_rate_limit,
)
from ..models.user import User
from ..models.stat import Stat
from ..core.constant import DEFAULT_STATS
from ..schemas.user import UserCreate, UserRead, Token, RefreshRequest
from ..models.boss import Boss
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await enforce_rate_limit(
        redis, "register", client_ip(request), REGISTER_RATE_LIMIT, REGISTER_RATE_WINDOW
    )

    # username тоже unique в БД — без этой проверки занятый ник давал бы
    # IntegrityError и 500 вместо внятной ошибки.
    result = await db.execute(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    existing = result.scalars().first()
    if existing is not None:
        detail = (
            "Email already registered"
            if existing.email == data.email
            else "Username already taken"
        )
        raise HTTPException(status_code=400, detail=detail)

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
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Лимит по IP, а не по username: иначе перебором чужого ника можно было бы
    # заблокировать вход владельцу аккаунта.
    ip = client_ip(request)
    await check_rate_limit(redis, "login", ip, LOGIN_FAILURE_LIMIT)

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        await record_attempt(redis, "login", ip, LOGIN_FAILURE_WINDOW)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Пароль подошёл — накопленные промахи с этого IP больше не держим,
    # иначе сосед по NAT мог бы исчерпать чужой лимит.
    await reset_rate_limit(redis, "login", ip)

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

