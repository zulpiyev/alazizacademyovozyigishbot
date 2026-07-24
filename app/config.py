from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RequiredChannel:
    chat_id: int | str
    name: str
    url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Lokal ishga tushirishda .env eski Windows muhit qiymatlaridan
        # ustun turadi. Railway'da esa Service Variables doimo ustun turadi.
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
            return (
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(default="sqlite:///data/alaziz_voting.db", alias="DATABASE_URL")
    admin_ids_csv: str = Field(default="", alias="ADMIN_IDS")
    timezone: str = Field(default="Asia/Tashkent", alias="TIMEZONE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    seed_demo_competition: bool = Field(default=False, alias="SEED_DEMO_COMPETITION")
    scheduler_interval_seconds: int = Field(
        default=60, alias="SCHEDULER_INTERVAL_SECONDS"
    )
    required_channel_1_id: str = Field(
        default="@alaziz_academy", alias="REQUIRED_CHANNEL_1_ID"
    )
    required_channel_1_name: str = Field(
        default="Al-Aziz Academy", alias="REQUIRED_CHANNEL_1_NAME"
    )
    required_channel_1_url: str = Field(
        default="https://t.me/alaziz_academy", alias="REQUIRED_CHANNEL_1_URL"
    )
    required_channel_2_id: str = Field(
        default="@abdulaziz_avazovichY", alias="REQUIRED_CHANNEL_2_ID"
    )
    required_channel_2_name: str = Field(
        default="Abdulaziz Avazovich", alias="REQUIRED_CHANNEL_2_NAME"
    )
    required_channel_2_url: str = Field(
        default="https://t.me/abdulaziz_avazovichY", alias="REQUIRED_CHANNEL_2_URL"
    )
    instagram_name: str = Field(
        default="Instagram — @alazizacademy", alias="INSTAGRAM_NAME"
    )
    instagram_url: str = Field(
        default="https://www.instagram.com/alazizacademy/", alias="INSTAGRAM_URL"
    )

    @staticmethod
    def _normalize_channel_id(value: str) -> int | str:
        cleaned = value.strip()
        if cleaned.startswith("-100") and cleaned.lstrip("-").isdigit():
            return int(cleaned)
        return cleaned

    @staticmethod
    def _channel_url(chat_id: int | str, configured_url: str) -> str:
        if configured_url.strip():
            return configured_url.strip()
        if isinstance(chat_id, str) and chat_id.startswith("@"):
            return f"https://t.me/{chat_id[1:]}"
        return "https://t.me/"

    @property
    def required_channels(self) -> tuple[RequiredChannel, ...]:
        channels: list[RequiredChannel] = []
        raw_items = (
            (self.required_channel_1_id, self.required_channel_1_name, self.required_channel_1_url),
            (self.required_channel_2_id, self.required_channel_2_name, self.required_channel_2_url),
        )
        for raw_id, raw_name, raw_url in raw_items:
            if not raw_id.strip():
                continue
            chat_id = self._normalize_channel_id(raw_id)
            channels.append(
                RequiredChannel(
                    chat_id=chat_id,
                    name=raw_name.strip() or str(chat_id),
                    url=self._channel_url(chat_id, raw_url),
                )
            )
        return tuple(channels)

    @property
    def admin_ids(self) -> list[int]:
        return [
            int(item.strip()) for item in self.admin_ids_csv.split(",") if item.strip()
        ]

    @property
    def async_database_url(self) -> str:
        url = make_url(self.database_url)
        if url.drivername in {"sqlite", "sqlite3"}:
            database = url.database or "data/alaziz_voting.db"
            database_path = Path(database)
            if not database_path.is_absolute():
                database_path = ROOT_DIR / database_path
            database_path.parent.mkdir(parents=True, exist_ok=True)
            url = url.set(drivername="sqlite+aiosqlite", database=str(database_path))
        return url.render_as_string(hide_password=False)

    @property
    def is_sqlite(self) -> bool:
        return make_url(self.async_database_url).drivername.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
