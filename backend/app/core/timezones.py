"""Работа с часовым поясом пользователя.

Все моменты времени в БД хранятся в UTC — это не меняется. Но «день» в
трекере привычек обязан быть днём пользователя, а не UTC: у игрока в МСК
сутки по UTC заканчиваются в 03:00 ночи, и привычка, закрытая в час ночи,
без пересчёта попадала бы во вчера и рвала серию.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_TIMEZONE = "UTC"


def is_valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def resolve_zone(name: str | None) -> ZoneInfo:
    """ZoneInfo по IANA-имени, с откатом на UTC.

    Пояс мог быть валидным на момент сохранения и исчезнуть после обновления
    базы tzdata — ронять из-за этого запрос нельзя.
    """
    if not name:
        return ZoneInfo(DEFAULT_TIMEZONE)
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TIMEZONE)


def local_now(zone: ZoneInfo) -> datetime:
    """Текущий момент, выраженный в поясе пользователя."""
    return datetime.now(zone)


def local_today(zone: ZoneInfo) -> date:
    """Календарная дата «сегодня» с точки зрения пользователя."""
    return datetime.now(zone).date()


async def get_user_zone(db: AsyncSession, user_id: int) -> ZoneInfo:
    """Пояс пользователя одним скалярным запросом.

    User импортируется внутри функции: models.user берёт отсюда
    DEFAULT_TIMEZONE, и импорт на уровне модуля замкнул бы цикл.
    """
    from ..models.user import User

    result = await db.execute(select(User.timezone).where(User.id == user_id))
    return resolve_zone(result.scalar_one_or_none())


def to_local_date(moment: datetime | None, zone: ZoneInfo) -> date | None:
    """Дата UTC-момента из БД в поясе пользователя.

    Наивные значения считаем UTC: так они и записывались до появления
    timezone=True у колонок.
    """
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo("UTC"))
    return moment.astimezone(zone).date()
