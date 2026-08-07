from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from ..models.quest import QuestType, QuestStatus


def _validate_scheduled_days(value: list[int] | None) -> list[int] | None:
    if value is None:
        return value
    if not all(0 <= day <= 6 for day in value):
        raise ValueError("scheduled_days must contain weekday numbers 0 (Пн) .. 6 (Вс)")
    normalized = sorted(set(value))
    if not normalized:
        raise ValueError("scheduled_days cannot be an empty list — omit the field instead")
    return normalized


class QuestBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    tag_id: int | None = None
    stat_id: int | None = None
    stat_id_2: int | None = None
    quest_type: QuestType = QuestType.once
    date_end: datetime | None = None
    scheduled_days: list[int] | None = None

    @field_validator("scheduled_days")
    @classmethod
    def check_scheduled_days(cls, value: list[int] | None) -> list[int] | None:
        return _validate_scheduled_days(value)

    @model_validator(mode="after")
    def check_stats_and_schedule(self):
        if self.stat_id is not None and self.stat_id == self.stat_id_2:
            raise ValueError("stat_id and stat_id_2 must be different stats")
        if self.scheduled_days is not None and self.quest_type != QuestType.habit:
            raise ValueError("scheduled_days is only allowed for habit quests")
        return self


class QuestCreate(QuestBase):
    pass


class QuestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    tag_id: int | None = None
    stat_id: int | None = None
    stat_id_2: int | None = None
    date_end: datetime | None = None
    scheduled_days: list[int] | None = None

    @field_validator("scheduled_days")
    @classmethod
    def check_scheduled_days(cls, value: list[int] | None) -> list[int] | None:
        return _validate_scheduled_days(value)

    @model_validator(mode="after")
    def check_stats_differ(self):
        if self.stat_id is not None and self.stat_id == self.stat_id_2:
            raise ValueError("stat_id and stat_id_2 must be different stats")
        return self


class QuestRead(QuestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int 
    user_id: int
    date_start: datetime
    status: QuestStatus
    reward_currency: int
    reward_xp: int
    current_streak: int
    best_streak: int
