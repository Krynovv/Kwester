from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import user, auth, quests, stats, tags, reward, boss
from .core.config import settings

app = FastAPI(title="Kwester")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(quests.router)
app.include_router(stats.router)
app.include_router(tags.router)
app.include_router(reward.router)
app.include_router(user.router)
app.include_router(boss.router)
