"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: The name of the application.
        debug: Whether debug mode is enabled.
        telegram_bot_token: The Telegram bot API token.
        openai_api_key: The OpenAI API key for GPT-4o vision.
        openai_model: The OpenAI model used for boleto extraction.
        database_url: The database connection URL.
    """

    app_name: str = "BillBot"
    debug: bool = False
    telegram_bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    database_url: str = "sqlite+aiosqlite:///billbot.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Load the application settings once.

    Only entrypoints should call this; everything else receives its
    configuration through constructor arguments.

    Returns:
        The cached Settings instance.
    """
    return Settings()
