from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database (built from individual vars for Docker compatibility)
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_user: str = "champion07"
    postgres_password: str = "change_me_in_production"  # noqa: S105
    postgres_db: str = "data-world-cup"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "change_me_in_production"  # noqa: S105
    minio_secure: bool = False
    minio_bucket_raw: str = "raw"
    minio_bucket_parquet: str = "parquet"

    # Ingestion
    csv_source_path: str = "./data_raw"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
