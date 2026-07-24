from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")  # опечатка в env/yaml -> явная ошибка при старте, а не тихий игнор

    TITLE: Annotated[str, Field(default="AppTitle", description="The title of the application")]
    HOST: Annotated[str, Field(default="0.0.0.0", description="The host of the application")]
    PORT: Annotated[int, Field(default=8000, ge=1, le=65535, description="The port of the application")]

    # Безопасный дефолт: если конфиг для прода почему-то не подхватится,
    # приложение не должно случайно подняться с включённым debug-режимом.
    # DEBUG=True нужно явно указывать в dev.yaml / .env.dev.
    DEBUG: Annotated[bool, Field(default=False, description="Debug mode")]

    LOG_LEVEL: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        Field(default="INFO", description="Log level"),
    ]