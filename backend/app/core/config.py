from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mariadb_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("FD_MARIADB_HOST", "DB_HOST"),
    )
    mariadb_port: int = Field(
        default=3306,
        validation_alias=AliasChoices("FD_MARIADB_PORT", "DB_PORT"),
    )
    mariadb_user: str = Field(
        default="root",
        validation_alias=AliasChoices("FD_MARIADB_USER", "DB_USER"),
    )
    mariadb_password: str = Field(
        default="",
        validation_alias=AliasChoices("FD_MARIADB_PASSWORD", "DB_PASSWORD"),
    )
    mariadb_database: str = Field(
        default="financial_dashboard",
        validation_alias=AliasChoices("FD_MARIADB_DATABASE", "DB_NAME"),
    )

    model_config = SettingsConfigDict(
        env_prefix="FD_",
        env_file=(
            str(Path(__file__).resolve().parents[2] / ".db.env"),
            str(Path(__file__).resolve().parents[2] / ".env"),
            str(Path(__file__).resolve().parents[3] / ".db.env"),
            str(Path(__file__).resolve().parents[3] / ".env"),
        ),
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
