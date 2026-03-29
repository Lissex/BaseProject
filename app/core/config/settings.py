from pathlib import Path

from pydantic_settings import (BaseSettings, SettingsConfigDict,
                               YamlConfigSettingsSource)

from app.core.config.modules.app import AppConfig
from app.core.config.modules.database import DatabaseConfig

"""Пути до папки настроек"""
CONFIG_PATH = Path(__file__).resolve().parent
ENVS_DIR = CONFIG_PATH / "envs"
YAML_DIR = CONFIG_PATH / "yaml"




class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP__", # Префикс который нужно будет писать в env
        case_sensitive=False, # Убираем чувствительность к регистру
        env_nested_delimiter="__", # Два подчеркивания
        env_file=(ENVS_DIR / ".env"), # .env - env файл откуда будут подтягиваться настройки
        yaml_config_section="restik", # Секция которая будеть браться из yaml файла
        yaml_file=(YAML_DIR / ".default.yaml"), # .yaml - yaml файл откуда будут подтягиваться настройки
    )

    app: AppConfig
    db: DatabaseConfig


    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls, deep_merge=True),
        )


settings = Settings()
