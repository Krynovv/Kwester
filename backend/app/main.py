from fastapi import FastAPI
from .routers import auth, quests, stats, tags

app = FastAPI(title="Kwester")

app.include_router(auth.router)
app.include_router(quests.router)
app.include_router(stats.router)
app.include_router(tags.router)
