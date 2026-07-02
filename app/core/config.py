from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Travel App"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./travel.db"
    ARTIC_API_URL: str = "https://api.artic.edu/api/v1"

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()