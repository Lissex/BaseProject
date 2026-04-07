from typing import Annotated

from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import URL


class DatabaseConfig(BaseModel):
    USERNAME: Annotated[str, Field(default="postgres", description="The username")]
    PASSWORD: Annotated[SecretStr, Field(description="The password")]  # ← секрет, нет дефолта
    DATABASE: Annotated[str, Field(default="restik_db", description="The database name")]
    HOST: Annotated[str, Field(default="localhost", description="The database host")]
    PORT: Annotated[int, Field(default=5432, description="The database port")]
    DRIVER: Annotated[str, Field(default="postgresql+asyncpg", description="The driver")]
    ECHO: Annotated[bool, Field(default=False, description="Enable SQLAlchemy echo")]

    @property
    def url(self) -> URL:
        return URL.create(
            drivername=self.DRIVER,
            username=self.USERNAME,
            password=self.PASSWORD.get_secret_value(),
            database=self.DATABASE,
            host=self.HOST,
            port=self.PORT,
        )