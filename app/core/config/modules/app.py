from typing import Annotated

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    TITLE: Annotated[str, Field(default="AppTitle", description="The title of the application")]
    HOST: Annotated[str, Field(default="0.0.0.0", description="The host of the application")]
    PORT: Annotated[int, Field(default=8000, description="The port of the application")]

    DEBUG: Annotated[bool, Field(default=True, description="Debug mode")]
    
    LOG_LEVEL: Annotated[str, Field(default="INFO", description="Log level")]

