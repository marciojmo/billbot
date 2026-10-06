"""Telegram bot polling mode entrypoint."""

import logging

from telegram import Update
from telegram.ext import Application

from app.bot.handlers import register_handlers
from app.container import ConfigurationError, Container, build_container, validate_settings
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

CONTAINER_KEY = "container"


def create_application(settings: Settings) -> Application:
    """Build the polling application with dependency lifecycle hooks.

    Args:
        settings: The application settings.

    Returns:
        The configured python-telegram-bot application.
    """

    async def post_init(application: Application) -> None:
        container = await build_container(settings, bot=application.bot)
        await container.start()
        application.bot_data[CONTAINER_KEY] = container
        register_handlers(application, container.queue)
        logger.info("Starting bot in polling mode...")

    async def post_shutdown(application: Application) -> None:
        container: Container | None = application.bot_data.get(CONTAINER_KEY)
        if container:
            await container.aclose()

    return (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )


def main() -> None:
    """Run the bot in polling mode."""
    settings = get_settings()
    configure_logging(settings.debug)

    try:
        validate_settings(settings)
    except ConfigurationError as e:
        logger.error("%s", e)
        raise SystemExit(1) from e

    create_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
