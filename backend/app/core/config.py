"""Application settings — loaded from environment / .env via Pydantic Settings v2."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf_8", 
    case_sensitive=False,
    extra="ignore",
  )
  #?? === App === #
  APP_NAME: str = "FIFA World Cup Platform API"
  APP_VERSION: str = "0.1.0"
  ENVIRONMENT: Literal["development", "staging", "production"] = "development"
  DEBUG: bool = False
  LOG_LEVEL: str = "INFO"
  #TODO === Server === #
  HOST: str = "0.0.0.0"  # noqa: S104
  PORT: int = 8000
  WORKERS: int = 1
  RELOAD: bool = False
  #* === Database === #
  DATABASE_URL: PostgresDsn = PostgresDsn (
     "postgresql+asyncpg://fifa:fifa_pass@localhost:5432/fifa_db"
  )
  DATABASE_POOL_SIZE: int = 20
  DATABASE_MAX_OVERFLOW: int = 10
  DATABASE_POOL_TIMEOUT: int = 30
  DATABASE_ECHO: bool = False

  #! === Redis (Db Caché) === #
  REDIS_URL: RedisDsn = RedisDsn("redis://localhost:6379/0")
  CACHE_TTL_SECONDS: int = 300 # 5 min Default

  #* === JWT (JSON Web Tokens) === #
  JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_32+_random_chars"  # noqa: S105
  JWT_ALGORITHM: str = "HS256"
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
  JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

  #* === AUTH Cookies === #
  REFRESH_COOKIES_NAME: str = "refresh_token"
  REFRESH_COOKIE_PATH: str = "/api/v1/auth/refresh"
  REFRESH_COOKIE_HTTPONLY: bool = True
  REFRESH_COOKIE_SECURE: bool = True
  REFRESH_COOKIE_SAMESITE: Literal["strict", "lax", "none"] = "lax"

  #! === CORS ( Conexión con Navegadores / Browser ) === #
  CORS_ORIGIN: list[AnyHttpUrl | str] = ["http://localhost:3000", "http://localhost:5173"]
  CORS_ALLOW_CREDENTIALS: bool = True

  #! === Rate Limiting (Límite de 'Request' / Peticiones) === #
  RATE_LIMIT_PUBLIC: int = 30  # req/min
  RATE_LIMIT_AUT: int = 10 # req/min

  #* === DB: MinIO / Storage s3 === # 
  STORAGE_ENDPOINT: str = "localhost:9000"
  STORAGE_ACCESS_KEY: str = "minioadmin"
  STORAGE_SECRET_KEY: str = "minioadmin"  # noqa: S105
  STORAGE_BUCKET: str = "fifa-data"
  STORAGE_SECURE: bool = False

  #! === Celery / ARQ (ETL async) === #
  BROKER_URL: str = "redis://localhost:6379/1"

  #?? ── Docs ─────────────────────────────────────────────────────────────────
  @property
  def docs_enable(self) -> bool:
      return self.ENVIRONMENT in ("development", "staging")
  
  #?? ── Validators ───────────────────────────────────────────────────────────

  @field_validator("JWT_SECRET_KEY")
  @classmethod
  def validate_secret_key(cls, v:str) -> str:
     if len(v) < 32:  # noqa:PLR2004
          raise ValueError("jwt_secret_key must be at least 32 characters (Debe tener al menos 32 caracteres.)")  # noqa: E501
     return v
  
  @model_validator(mode="after")
  def secure_cookie_in_production(self) ->  Settings:
      if self.ENVIRONMENT == "production" and not self.REFRESH_COOKIE_SECURE:
        raise ValueError("REFRESH_COOKIE_SECURE must be True in production")
      return self
  
  @property
  def db_url_str(self) -> str: 
      return str(self.DATABASE_URL)

  @property
  def db_redis_url_str(self) -> str:
      return str(self.REDIS_URL)


@lru_cache(maxsize=1)
def get_setting() -> Settings: 
    return Settings()