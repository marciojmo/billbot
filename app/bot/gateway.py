"""Outbound Telegram API calls."""

import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramGateway:
    """Downloads files and sends messages through a Telegram bot."""

    def __init__(self, bot: Bot) -> None:
        """Create the gateway.

        Args:
            bot: An initialized python-telegram-bot Bot.
        """
        self._bot = bot

    async def download_file(self, file_id: str) -> bytes | None:
        """Download a file from Telegram servers.

        Args:
            file_id: The Telegram file ID.

        Returns:
            The file content, or None if the download failed.
        """
        try:
            file = await self._bot.get_file(file_id)
            return bytes(await file.download_as_bytearray())
        except TelegramError as e:
            logger.error("Failed to download file %s: %s", file_id, e)
            return None

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to: int | None = None,
        markdown: bool = True,
    ) -> None:
        """Send a message to a chat.

        Args:
            chat_id: The target chat ID.
            text: The message text.
            reply_to: Optional message ID to reply to.
            markdown: Whether to render the text as Markdown.
        """
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN if markdown else None,
            reply_to_message_id=reply_to,
        )
