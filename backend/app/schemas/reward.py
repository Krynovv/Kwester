from pydantic import BaseModel, ConfigDict, Field

class RewardBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    cost: int = Field(gt=0)
    unlock_level: int = Field(default=0, ge=0)

class RewardCreate(RewardBase):
    pass

class RewardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    cost: int | None = Field(default=None, gt=0)
    unlock_level: int | None = Field(default=None, ge=0)

class RewardRead(RewardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_purchased: bool
