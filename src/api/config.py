"""MongoDB Configurations."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    mongodb_uri: str = Field(validation_alias=AliasChoices("MONGODB_URI"))
    nws_config_path: str | None = Field(
        default=None, validation_alias=AliasChoices("NWS_CONFIG_PATH")
    )

    class Config:
        """Configuration for the settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
