"""Отправка сообщений в Telegram и проверка подписи Mini App initData.

BOT_TOKEN опционален (см. core/config.py) — модуль не падает при импорте без
него, но get_bot()/verify_init_data() без токена вызывать нельзя.
"""

from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

from ..core.config import settings

_bot: Bot | None = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        if settings.bot_token is None:
            raise RuntimeError("BOT_TOKEN is not configured")
        _bot = Bot(token=settings.bot_token.get_secret_value())
    return _bot


async def close_bot() -> None:
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None


def verify_init_data(init_data: str, max_age_seconds: int = 86400) -> WebAppInitData | None:
    """Проверяет подпись initData и её свежесть. None — если что-то не так.

    safe_parse_webapp_init_data проверяет только HMAC-подпись, не возраст —
    без отдельной проверки auth_date однажды утёкшая строка была бы валидна
    вечно.
    """
    if settings.bot_token is None:
        return None
    try:
        data = safe_parse_webapp_init_data(settings.bot_token.get_secret_value(), init_data)
    except ValueError:
        return None
    age = (datetime.now(timezone.utc) - data.auth_date).total_seconds()
    if age > max_age_seconds:
        return None
    return data


async def send_message(chat_id: int, text: str) -> bool:
    try:
        await get_bot().send_message(chat_id, text)
        return True
    except TelegramAPIError:
        # Заблокировал бота, chat_id стал невалиден и т.п. — одна неудачная
        # отправка не должна ронять цикл напоминаний для остальных.
        return False
