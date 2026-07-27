from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class JWTConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    SECRET_KEY: Annotated[SecretStr, Field(description="Секрет для подписи access-токенов")]
    ALGORITHM: Annotated[str, Field(default="HS256", description="Алгоритм подписи JWT")]

    ACCESS_TOKEN_EXPIRE_MINUTES: Annotated[
        int, Field(default=15, ge=1, description="Время жизни access-токена, минуты")
    ]
    REFRESH_TOKEN_EXPIRE_DAYS: Annotated[
        int, Field(default=30, ge=1, description="Время жизни refresh-токена, дни")
    ]