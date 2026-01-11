"""Queue message consumers for async processing."""

import logging

import httpx

from app.core.config import settings
from app.schemas.queue import QueueMessage
from app.services.ocr_service import extract_boleto_data
from app.services.pdf_service import convert_pdf_to_images
from app.services.storage import store_boleto

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
PDF_MIME_TYPES = {"application/pdf"}


async def download_file(file_id: str) -> bytes | None:
    """Download a file from Telegram servers.

    Args:
        file_id: The Telegram file ID.

    Returns:
        The file content as bytes, or None if download failed.
    """
    token = settings.telegram_bot_token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TELEGRAM_API_BASE}/bot{token}/getFile",
            params={"file_id": file_id},
        )
        data = response.json()

        if not data.get("ok"):
            logger.error(f"Failed to get file info: {data}")
            return None

        file_path = data["result"]["file_path"]
        file_response = await client.get(
            f"{TELEGRAM_API_BASE}/file/bot{token}/{file_path}"
        )
        return file_response.content


async def send_reply(chat_id: int, text: str, reply_to: int | None = None) -> None:
    """Send a reply message to Telegram.

    Args:
        chat_id: The chat ID to send to.
        text: The message text.
        reply_to: Optional message ID to reply to.
    """
    token = settings.telegram_bot_token
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API_BASE}/bot{token}/sendMessage", json=payload)


async def process_image_bytes(
    image_bytes: bytes,
    telegram_id: int,
    first_name: str | None,
    username: str | None,
) -> None:
    """Process image bytes, extract boleto data and store it.

    Args:
        image_bytes: The image content as bytes.
        telegram_id: The Telegram user ID.
        first_name: User's first name.
        username: User's Telegram username.
    """
    try:
        boleto_data = await extract_boleto_data(image_bytes)
        await store_boleto(boleto_data, telegram_id, first_name, username)
    except ValueError as e:
        logger.error(f"OCR error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing image: {e}")


async def ocr_consumer(msg: QueueMessage) -> None:
    """Consumer that processes files with OCR.

    Args:
        msg: The queue message to process.
    """
    if msg.type == "text" or not msg.file:
        return

    logger.info(f"OCR consumer processing message {msg.id}")

    file_bytes = await download_file(msg.file.file_id)
    if not file_bytes:
        await send_reply(
            msg.chat.id,
            "Não consegui baixar o arquivo, você poderia enviá-lo novamente?",
            msg.message.id,
        )
        return

    if msg.file.mime_type in PDF_MIME_TYPES:
        logger.info("Detected PDF, converting pages to images...")
        try:
            images = convert_pdf_to_images(file_bytes)
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            await send_reply(
                msg.chat.id,
                "Não consegui abrir esse PDF. Será que o arquivo está correto?",
                msg.message.id,
            )
            return

        if not images:
            await send_reply(
                msg.chat.id,
                "Não encontrei nenhuma página nesse PDF. Pode verificar o arquivo?",
                msg.message.id,
            )
            return

        for i, image_bytes in enumerate(images):
            logger.info(f"Processing PDF page {i + 1}/{len(images)}")
            await process_image_bytes(
                image_bytes,
                msg.user.telegram_id,
                msg.user.first_name,
                msg.user.username,
            )
    else:
        await process_image_bytes(
            file_bytes,
            msg.user.telegram_id,
            msg.user.first_name,
            msg.user.username,
        )

    logger.info(f"OCR consumer finished processing message {msg.id}")


async def logger_consumer(msg: QueueMessage) -> None:
    """Consumer that logs messages for debugging.

    Args:
        msg: The queue message to log.
    """
    logger.info(
        f"[LOG] Message {msg.id}: type={msg.type}, "
        f"user={msg.user.first_name} (@{msg.user.username}), "
        f"chat={msg.chat.id}, file={msg.file.file_id if msg.file else None}"
    )
