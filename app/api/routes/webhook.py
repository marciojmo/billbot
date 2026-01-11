"""Telegram webhook route handlers."""

import httpx
from fastapi import APIRouter, BackgroundTasks, status
from telegram import Update

from app.core.config import settings
from app.schemas.telegram import TelegramUpdate
from app.services.command_handler import get_start_message
from app.services.message_handler import process_document, process_photo

router = APIRouter(prefix="/webhook", tags=["webhook"])

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def send_telegram_message(
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
) -> None:
    """Send a message to a Telegram chat.

    Args:
        chat_id: The target chat ID.
        text: The message text to send.
        parse_mode: Optional parse mode (Markdown, HTML).
    """
    url = TELEGRAM_API_URL.format(token=settings.telegram_bot_token)
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)


async def process_and_respond(
    update: Update,
    chat_id: int,
) -> None:
    """Process an update and send the response.

    Args:
        update: The Telegram update to process.
        chat_id: The chat ID to respond to.
    """
    message = update.message
    if not message:
        return

    await send_telegram_message(chat_id, "🔄 Processando boleto...")

    if message.document:
        response = await process_document(message)
    elif message.photo:
        response = await process_photo(message)
    else:
        return

    await send_telegram_message(chat_id, response, parse_mode="Markdown")


@router.post(
    "/telegram",
    status_code=status.HTTP_200_OK,
    summary="Receive Telegram updates",
    description="Webhook endpoint for receiving updates from Telegram.",
)
async def receive_telegram_update(
    update: TelegramUpdate,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Receive and process a Telegram update.

    Args:
        update: The raw Telegram update payload.
        background_tasks: FastAPI background tasks for async processing.

    Returns:
        A status message indicating the update was received.
    """
    telegram_update = Update.de_json(update.to_dict(), bot=None)

    if telegram_update.message:
        message = telegram_update.message
        name = message.from_user.first_name if message.from_user else "usuário"
        chat_id = message.chat.id

        if message.document or message.photo:
            background_tasks.add_task(
                process_and_respond,
                telegram_update,
                chat_id,
            )
        else:
            await send_telegram_message(chat_id, get_start_message(name))

    return {"status": "ok"}
