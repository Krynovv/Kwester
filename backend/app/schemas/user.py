from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from ..core.timezones import DEFAULT_TIMEZONE, is_valid_timezone


def _validate_timezone(value: str | None) -> str | None:
    if value is None:
        return value
    if not is_valid_timezone(value):
        raise ValueError("timezone must be a valid IANA name, e.g. Europe/Moscow")
    return value


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    # Фронт подставляет пояс браузера при регистрации; UTC — запасной вариант
    # для клиентов, которые его не прислали.
    timezone: str = DEFAULT_TIMEZONE

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return _validate_timezone(value)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    image_file: str | None = None
    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str | None) -> str | None:
        return _validate_timezone(value)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TelegramLinkRequest(BaseModel):
    # Сырая подписанная строка window.Telegram.WebApp.initData — проверяется
    # на бэкенде через BOT_TOKEN, клиенту доверять нельзя (см. service/telegram.py).
    init_data: str = Field(min_length=1)

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    image_file: str | None = None
    currency_balance: int
    current_hp: int
    boss_currency_balance: int
    timezone: str
    # Не выставляется через общий PATCH /users/me — только через
    # POST /users/me/telegram, где id проверяется подписью бота.
    telegram_chat_id: int | None = None

