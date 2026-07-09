from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict
from ..models.quest import QuestType, QuestStatus

class QuestBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    tag_id: int | None = None
    stat_id: int | None = None
    quest_type: QuestType = QuestType.once
    date_end: datetime | None = None

class QuestCreate(QuestBase):
    pass

class QuestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    tag_id: int | None = None
    stat_id: int | None = None
    date_end: datetime | None = None

class QuestRead(QuestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int 
    user_id: int
    date_start: datetime
    status: QuestStatus
    reward_currency: int
    reward_xp: int

