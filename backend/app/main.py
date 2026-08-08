import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .routers import user, auth, quests, stats, tags, reward, boss, shop
from .core.config import settings
from .core.constant import MAX_REQUEST_BODY_SIZE

app = FastAPI(title="Kwester")


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    """Отсекает слишком большие тела до того, как их разберёт Starlette.

    Проверка внутри эндпоинта опоздала бы: к моменту вызова обработчика
    multipart уже полностью записан во временный файл.
    """
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid Content-Length header"},
            )
        if declared_size > MAX_REQUEST_BODY_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={"detail": "Request body too large"},
            )
    return await call_next(request)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.image_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(auth.router)
app.include_router(quests.router)
app.include_router(stats.router)
app.include_router(tags.router)
app.include_router(reward.router)
app.include_router(user.router)
app.include_router(boss.router)
app.include_router(shop.router)
