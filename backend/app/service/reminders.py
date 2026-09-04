"""Проактивная рассылка Telegram-напоминаний по привычкам с reminder_times.

В отличие от остального service/quest.py (там всё лениво досчитывается на
GET /quest), напоминание обязано прийти, даже если пользователь не открывал
приложение — поэтому этот модуль вызывается по таймеру из app/main.py, а не
из роутера.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..core.timezones import resolve_zone, local_now, to_local_date
from ..models.quest import Quest, QuestStatus, QuestType
from ..models.user import User
from .telegram import send_message

logger = logging.getLogger(__name__)


async def send_due_habit_reminders(session_factory: async_sessionmaker) -> None:
    async with session_factory() as db:
        result = await db.execute(
            select(Quest, User)
            .join(User, Quest.user_id == User.id)
            .where(
                Quest.quest_type == QuestType.habit,
                Quest.status == QuestStatus.active,
                Quest.reminder_times.is_not(None),
                User.telegram_chat_id.is_not(None),
            )
        )

        for quest, user in result.all():
            zone = resolve_zone(user.timezone)
            now = local_now(zone)
            today = now.date()

            due_time = (quest.reminder_times or {}).get(str(now.weekday()))
            if due_time is None or now.strftime("%H:%M") < due_time:
                continue

            if quest.last_completed_at and to_local_date(quest.last_completed_at, zone) == today:
                continue  # уже выполнено сегодня — напоминать незачем

            # Атомарный UPDATE вместо read-then-write: если бэкенд когда-нибудь
            # запустят в нескольких процессах, только один из них отправит
            # сообщение за конкретный день.
            claimed = await db.execute(
                update(Quest)
                .where(Quest.id == quest.id, Quest.last_notified_date.is_distinct_from(today))
                .values(last_notified_date=today)
                .returning(Quest.id)
            )
            if claimed.scalar_one_or_none() is None:
                continue
            await db.commit()

            sent = await send_message(user.telegram_chat_id, f"⏰ «{quest.name}» — время для привычки!")
            if not sent:
                logger.warning("Failed to send habit reminder: user_id=%s quest_id=%s", user.id, quest.id)
