from pydantic import BaseModel, Field, ConfigDict

class StatBase(BaseModel):
    name: str = Field(min_length=1, max_length=30)

class StatCreate(StatBase):
    pass

class StatUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)

class StatRead(StatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    level: int
    current_xp: int
    xp_to_next_level: int  
