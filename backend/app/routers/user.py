import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.database import get_db
from ..core.config import settings
from ..core.constant import ALLOWED_AVATAR_TYPES, MAX_AVATAR_SIZE
from ..models.user import User
from ..schemas.user import UserRead

router = APIRouter(prefix = "/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
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
