import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.redis import get_redis


class FakeRedis:
    """Заглушка Redis на обычном словаре — живой сервер тестам не нужен.

    Кэширует по-настоящему: иначе тесты не проверяли бы инвалидацию
    в invalidate_boss_status и не ловили бы протухший статус после боя.
    TTL (ex) игнорируется — истечение по времени здесь не воспроизводится.
    """

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key):
        return self._data.get(key)

    async def set(self, key, value, ex=None):
        self._data[key] = value

    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)


@pytest.fixture
def fake_redis():
    return FakeRedis()


engine = create_async_engine(settings.test_database_url)
TestSession = async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture
async def db_session():
    async with TestSession() as session:
        yield session  
        await session.rollback()

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

@pytest.fixture
async def client(db_session, fake_redis):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
