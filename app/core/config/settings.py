from functools import lru_cache
from pathlib import Path
from typing import Literal

import os

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from app.core.config.modules.app import AppConfig
from app.core.config.modules.database import DatabaseConfig


# =========================
# 📁 Пути
# =========================
BASE_DIR = Path(__file__).resolve().parent
ENVS_DIR = BASE_DIR / "envs"
YAML_DIR = BASE_DIR / "yaml"


# =========================
# 🌍 Окружение
# =========================
class Environment(str):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


ENV: Literal["dev", "prod", "test"] = os.getenv("ENV", "dev")

ENV_FILE = ENVS_DIR / f".env.{ENV}"
YAML_FILE = YAML_DIR / f"{ENV}.yaml"


# =========================
# ⚙️ Settings
# =========================
class Settings(BaseSettings):
    environment: Literal["dev", "prod", "test"] = ENV

    app: AppConfig
    db: DatabaseConfig

    model_config = SettingsConfigDict(
        env_prefix="APP__",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=ENV_FILE,
        yaml_file=YAML_FILE,
        extra="ignore",  # важно для продакшена
    )

    # =========================
    # 🚩 Флаги окружения
    # =========================
    @property
    def is_dev(self) -> bool:
        return self.environment == "dev"

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    # =========================
    # 🔌 Источники (приоритет)
    # =========================
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,          # вручную переданные значения
            env_settings,           # переменные окружения
            dotenv_settings,        # .env файл
            file_secret_settings,   # docker secrets
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file=YAML_FILE, 
                deep_merge=True
                ),
        )

settings = Settings()