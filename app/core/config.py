from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Event Analytics & Reporting Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/event_analytics"
    REDIS_URL: str = "redis://localhost:6379/0"

    AWS_ACCESS_KEY_ID: str = "fake-key"
    AWS_SECRET_ACCESS_KEY: str = "fake-secret"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "event-analytics-archive"

    CACHE_TTL_DAILY: int = 300
    CACHE_TTL_MONTHLY: int = 600
    CACHE_TTL_SUMMARY: int = 300
    CACHE_TTL_TOP_SOURCES: int = 300

    ARCHIVE_DAYS_THRESHOLD: int = 90

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
