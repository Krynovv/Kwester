import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.database import get_db
from ..core.config import settings
from ..core.constant import ALLOWED_AVATAR_TYPES, MAX_AVATAR_SIZE
from ..models.user import User
from ..schemas.user import UserRead, UserUpdate

router = APIRouter(prefix = "/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # image_file исключён намеренно: его проставляет загрузка аватара, и
    # принимать имя файла от клиента незачем.
    update_data = data.model_dump(exclude_unset=True, exclude={"image_file"})

    # username и email уникальны в БД — без проверки занятое значение дало бы
    # IntegrityError и 500, как это было в регистрации.
    conflicts = [
        (User.username == update_data[field] if field == "username" else User.email == update_data[field])
        for field in ("username", "email")
        if field in update_data and update_data[field] != getattr(current_user, field)
    ]
    if conflicts:
        result = await db.execute(
            select(User).where(User.id != current_user.id, or_(*conflicts))
        )
        taken = result.scalars().first()
        if taken is not None:
            detail = (
                "Username already taken"
                if taken.username == update_data.get("username")
                else "Email already registered"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = ALLOWED_AVATAR_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

    # Читаем на байт больше лимита: превышение видно, а в память попадает
    # ограниченный объём даже при подделанном Content-Length.
    contents = await file.read(MAX_AVATAR_SIZE + 1)
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large (max 5MB)")

    os.makedirs(settings.image_dir, exist_ok=True)
    filename = f"{current_user.id}.{ext}"
    with open(os.path.join(settings.image_dir, filename), "wb") as f:
        f.write(contents)

    current_user.image_file = filename
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
