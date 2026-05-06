from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    postgres_dsn: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/fifa"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fifa"

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_raw: str = "raw"
    minio_bucket_parquet: str = "parquet"

    # Ingestion
    csv_source_path: str = "./data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
