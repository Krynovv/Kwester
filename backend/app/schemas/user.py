from datetime import datetime
import database
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=8, mac_length=72)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    image_file: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    image_file: str | None = None

