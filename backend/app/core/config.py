from warnings import deprecated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    app_name: str = "Kwester"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/qwester"
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/qwester_test"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
    ]
    static_dir: str = "static"
    image_dir: str = "static/images"

    model_config = SettingsConfigDict(env_file=".env")
    
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

settings = Settings()



