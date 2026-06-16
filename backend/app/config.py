from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://docapp:docapp_secret_2026@postgres:5432/documents_db"

    minio_host: str = "minio"
    minio_port: int = 9000
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin_secret_2026"
    minio_bucket: str = "documents"
    minio_url: str = "http://minio:9000"
    minio_public_url: str = "http://localhost:9000"

    redis_url: str = "redis://redis:6379"

    tesseract_lang: str = "spa"

    upload_max_size: int = 52428800

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
