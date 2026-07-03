
from pydantic import BaseModel, Field, ConfigDict

class TagBase(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    linked_stat_id: int | None = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    linked_stat_id: int | None = None

class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
