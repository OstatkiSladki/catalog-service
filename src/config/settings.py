from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Implements: spec://com.ostatki.catalog/PROP-001#foundation
class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

  app_name: str = Field(default="catalog-service")
  app_version: str = Field(default="1.0.0")
  app_env: str = Field(default="development")
  debug: bool = Field(default=False)
  app_root_path: str = Field(default="")

  host: str = Field(default="0.0.0.0")
  port: int = Field(default=8002)

  database_url: str = Field(
    default="postgresql+asyncpg://catalog:catalog@localhost:5432/db_catalog"
  )
  database_pool_size: int = Field(default=10)
  database_max_overflow: int = Field(default=20)
  database_pool_timeout: int = Field(default=30)

  log_level: str = Field(default="INFO")
  log_format: str = Field(default="json")

  @field_validator("debug", mode="before")
  @classmethod
  def normalize_debug(cls, value: object) -> bool:
    if isinstance(value, bool):
      return value
    if isinstance(value, str):
      return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()
