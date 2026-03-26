from typing import Annotated

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    TITLE: Annotated[str, Field(default="AppTitle", description="The title of the application")]
    HOST: Annotated[str, Field(default="0.0.0.0", description="The host of the application")]
    PORT: Annotated[int, Field(default=8000, description="The port of the application")]
    IS_DEV: Annotated[bool, Field(default=True, description="Is the app running in development mode")]
    LOG_LEVEL: Annotated[str, Field(default="INFO", description="The logging level")]
    LOG_FORMAT: Annotated[str, Field(default="terminal", description="The logging format")]
    # DEBUG: Annotated[bool, Field(default=False, description="Enable debug mode")]
    # ENVIRONMENT: Annotated[str, Field(default="development", description="The environment")]