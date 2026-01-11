"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: The name of the application.
        debug: Whether debug mode is enabled.
        telegram_bot_token: The Telegram bot API token.
        openai_api_key: The OpenAI API key for GPT-4o vision.
        database_url: The database connection URL.
    """

    app_name: str = "BillBot"
    debug: bool = False
    telegram_bot_token: str = ""
    openai_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///billbot.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
