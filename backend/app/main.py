from app.schemas import reward
from fastapi import FastAPI
from .routers import auth, quests, stats, tags, reward

app = FastAPI(title="Kwester")

app.include_router(auth.router)
app.include_router(quests.router)
app.include_router(stats.router)
app.include_router(tags.router)
app.include_router(reward.router)
