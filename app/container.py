"""Composition root: builds and wires the application's dependencies."""

from dataclasses import dataclass

from openai import AsyncOpenAI
from telegram import Bot

from app.bot.gateway import TelegramGateway
from app.core.config import Settings
from app.db.database import Database
from app.services.boletos import BoletoService
from app.services.ocr import BoletoExtractor
from app.worker.consumers import LoggingConsumer, OcrConsumer, ResponseConsumer
from app.worker.queue import MessageQueue


class ConfigurationError(Exception):
    """Raised when required settings are missing."""


@dataclass
class Container:
    """The application's long-lived dependencies.

    Attributes:
        settings: The application settings.
        database: The database.
        bot: The Telegram bot.
        queue: The message queue, already wired with its consumers.
    """

    settings: Settings
    database: Database
    bot: Bot
    queue: MessageQueue
    _openai: AsyncOpenAI
    _owns_bot: bool

    async def start(self) -> None:
        """Create database tables and start processing the queue."""
        await self.database.create_tables()
        self.queue.start()

    async def aclose(self) -> None:
        """Stop the queue and release all resources."""
        await self.queue.stop()
        await self._openai.close()
        if self._owns_bot:
            await self.bot.shutdown()
        await self.database.dispose()


def validate_settings(settings: Settings) -> None:
    """Check that the settings required to run the bot are present.

    Args:
        settings: The settings to validate.

    Raises:
        ConfigurationError: If a required setting is missing.
    """
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token),
            ("OPENAI_API_KEY", settings.openai_api_key),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


async def build_container(settings: Settings, bot: Bot | None = None) -> Container:
    """Build and wire all application dependencies.

    Args:
        settings: The application settings.
        bot: An already-initialized bot to reuse (e.g. the one owned by a
            python-telegram-bot Application). If omitted, a new bot is
            created, initialized and shut down by ``Container.aclose``.

    Returns:
        The wired container. Call ``start()`` before use.

    Raises:
        ConfigurationError: If a required setting is missing.
    """
    validate_settings(settings)

    owns_bot = bot is None
    if bot is None:
        bot = Bot(settings.telegram_bot_token)
        await bot.initialize()

    database = Database(settings.database_url, echo=settings.debug)
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    gateway = TelegramGateway(bot)
    extractor = BoletoExtractor(openai_client, model=settings.openai_model)
    boletos = BoletoService(database)

    queue = MessageQueue(
        [
            LoggingConsumer(),
            OcrConsumer(gateway, extractor, boletos),
            ResponseConsumer(gateway, boletos),
        ]
    )

    return Container(
        settings=settings,
        database=database,
        bot=bot,
        queue=queue,
        _openai=openai_client,
        _owns_bot=owns_bot,
    )
