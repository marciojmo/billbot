"""Queue message consumers for async processing."""

import asyncio
import logging
from typing import Protocol

from app.bot import messages
from app.bot.gateway import TelegramGateway
from app.schemas.queue import QueueMessage, UserInfo
from app.services.boletos import BoletoService
from app.services.ocr import BoletoExtractor
from app.services.pdf import render_pdf_pages

logger = logging.getLogger(__name__)

PDF_MIME_TYPES = {"application/pdf"}


class Consumer(Protocol):
    """A processing step run on every queue message."""

    name: str

    async def __call__(self, msg: QueueMessage) -> None:
        """Process a queue message.

        Args:
            msg: The queue message.
        """
        ...


class LoggingConsumer:
    """Logs every message for debugging."""

    name = "logging"

    async def __call__(self, msg: QueueMessage) -> None:
        """Log the message.

        Args:
            msg: The queue message to log.
        """
        logger.info(
            "[LOG] Message %s: type=%s, user=%s (@%s), chat=%s, file=%s",
            msg.id,
            msg.type,
            msg.user.first_name,
            msg.user.username,
            msg.chat.id,
            msg.file.file_id if msg.file else None,
        )


class OcrConsumer:
    """Downloads files, extracts boleto data and stores it."""

    name = "ocr"

    def __init__(
        self,
        gateway: TelegramGateway,
        extractor: BoletoExtractor,
        boletos: BoletoService,
    ) -> None:
        """Create the consumer.

        Args:
            gateway: Telegram gateway for downloads and error replies.
            extractor: Boleto extractor for images.
            boletos: Service that stores extracted boletos.
        """
        self._gateway = gateway
        self._extractor = extractor
        self._boletos = boletos

    async def __call__(self, msg: QueueMessage) -> None:
        """Process the file attached to a message, if any.

        Args:
            msg: The queue message to process.
        """
        if msg.type == "text" or not msg.file:
            return

        logger.info("OCR consumer processing message %s", msg.id)

        file_bytes = await self._gateway.download_file(msg.file.file_id)
        if not file_bytes:
            await self._reply(msg, messages.DOWNLOAD_FAILED)
            return

        if msg.file.mime_type in PDF_MIME_TYPES:
            logger.info("Detected PDF, converting pages to images...")
            try:
                images = await asyncio.to_thread(render_pdf_pages, file_bytes)
            except Exception:
                logger.exception("Failed to convert PDF")
                await self._reply(msg, messages.PDF_UNREADABLE)
                return

            if not images:
                await self._reply(msg, messages.PDF_EMPTY)
                return
        else:
            images = [file_bytes]

        for page_num, image_bytes in enumerate(images, start=1):
            logger.info("Processing image %d/%d", page_num, len(images))
            await self._process_image(image_bytes, msg.user)

        logger.info("OCR consumer finished processing message %s", msg.id)

    async def _process_image(self, image_bytes: bytes, user: UserInfo) -> None:
        """Extract and store one image, logging any failure.

        Args:
            image_bytes: The image content.
            user: The user who sent the image.
        """
        try:
            boleto_data = await self._extractor.extract(image_bytes)
            await self._boletos.store(boleto_data, user)
        except Exception:
            logger.exception("Failed to process image")

    async def _reply(self, msg: QueueMessage, text: str) -> None:
        """Reply to the original message.

        Args:
            msg: The queue message to reply to.
            text: The reply text.
        """
        await self._gateway.send_message(msg.chat.id, text, msg.message.id)


class ResponseConsumer:
    """Replies with the user's full boleto list."""

    name = "response"

    def __init__(self, gateway: TelegramGateway, boletos: BoletoService) -> None:
        """Create the consumer.

        Args:
            gateway: Telegram gateway for sending the reply.
            boletos: Service that lists stored boletos.
        """
        self._gateway = gateway
        self._boletos = boletos

    async def __call__(self, msg: QueueMessage) -> None:
        """Send the boleto list for file messages.

        Args:
            msg: The queue message.
        """
        if msg.type == "text":
            return

        boletos = await self._boletos.list_for_user(msg.user.telegram_id)
        await self._gateway.send_message(
            msg.chat.id, messages.format_boleto_list(boletos), msg.message.id
        )
