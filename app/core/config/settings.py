from enum import StrEnum
from functools import lru_cache
from pathlib import Path

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
class Environment(StrEnum):
    """
    Единый источник правды для допустимых окружений.
    Используется и как Literal-подобный тип, и как enum со значениями.
    """
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


def _resolve_env() -> Environment:
    """
    Читает ENV из переменных окружения и валидирует значение.

    Если ENV задан неправильно (опечатка, лишний пробел и т.п.),
    приложение должно упасть здесь и сразу, а не тихо откатиться
    на дефолтный конфиг где-нибудь в проде.
    """
    raw = os.getenv("ENV", Environment.DEV.value).strip().lower()
    try:
        return Environment(raw)
    except ValueError:
        allowed = ", ".join(e.value for e in Environment)
        raise RuntimeError(
            f"Invalid ENV={raw!r}. Allowed values: {allowed}"
        ) from None


ENV: Environment = _resolve_env()

ENV_FILE = ENVS_DIR / f".env.{ENV.value}"
YAML_FILE = YAML_DIR / f"{ENV.value}.yaml"

# В проде конфиги обязаны существовать — молчаливый fallback на дефолты
# в этом окружении недопустим (например, DatabaseConfig.PASSWORD всё равно
# обязателен и уронит приложение, но лучше явная и понятная ошибка сразу
# про отсутствующий файл, чем гадать по цепочке pydantic-ошибок).
if ENV is Environment.PROD:
    missing = [p for p in (ENV_FILE, YAML_FILE) if not p.exists()]
    if missing:
        names = ", ".join(str(p) for p in missing)
        raise RuntimeError(f"Missing required config file(s) for prod: {names}")


# =========================
# ⚙️ Settings
# =========================
class Settings(BaseSettings):
    environment: Environment = ENV

    app: AppConfig
    db: DatabaseConfig

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=ENV_FILE,
        yaml_file=YAML_FILE,
        extra="ignore",  # важно для продакшена: лишние переменные окружения не роняют приложение
    )

    # =========================
    # 🚩 Флаги окружения
    # =========================
    @property
    def is_dev(self) -> bool:
        return self.environment is Environment.DEV

    @property
    def is_prod(self) -> bool:
        return self.environment is Environment.PROD

    @property
    def is_test(self) -> bool:
        return self.environment is Environment.TEST

    # =========================
    # 🔌 Источники (приоритет: сверху важнее)
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
            init_settings,          # вручную переданные значения (напр. в тестах)
            env_settings,           # переменные окружения (APP_...)
            dotenv_settings,        # .env файл
            file_secret_settings,   # docker/k8s secrets из SECRETS_DIR
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file=YAML_FILE,
                deep_merge=True,
            ),                      # yaml — база/дефолты, самый низкий приоритет
        )


@lru_cache
def get_settings() -> Settings:
    """
    Кэшированная фабрика настроек.

    Используйте get_settings() (в т.ч. как FastAPI-зависимость) вместо
    прямого обращения к settings, если нужна возможность подменять
    конфиг в тестах через get_settings.cache_clear() + monkeypatch.
    """
    return Settings()


# Обратная совместимость / удобный доступ для мест, где DI не нужен
# (напр. app/infrastructure/database/engine.py: from ... import settings)
settings = get_settings()