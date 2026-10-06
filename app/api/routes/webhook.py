"""Telegram webhook route handlers."""

from fastapi import APIRouter, status
from telegram import Update

from app.api.dependencies import BotDep, GatewayDep, QueueDep
from app.bot import messages
from app.bot.mapper import to_queue_message
from app.schemas.telegram import TelegramUpdate

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post(
    "/telegram",
    status_code=status.HTTP_200_OK,
    summary="Receive Telegram updates",
    description="Webhook endpoint for receiving updates from Telegram.",
)
async def receive_telegram_update(
    update: TelegramUpdate,
    bot: BotDep,
    gateway: GatewayDep,
    queue: QueueDep,
) -> dict[str, str]:
    """Receive a Telegram update and route it like polling mode does.

    File messages are enqueued for processing; anything else gets the
    greeting.

    Args:
        update: The raw Telegram update payload.
        bot: The Telegram bot, used to deserialize the update.
        gateway: Telegram gateway for immediate replies.
        queue: The message queue.

    Returns:
        A status message indicating the update was received.
    """
    message = Update.de_json(update.to_dict(), bot).message
    if not message:
        return {"status": "ok"}

    chat_id = message.chat.id
    if not (message.document or message.photo):
        name = message.from_user.first_name if message.from_user else None
        await gateway.send_message(chat_id, messages.format_start(name), markdown=False)
        return {"status": "ok"}

    queue_msg = to_queue_message(message)
    if not queue_msg:
        await gateway.send_message(chat_id, messages.INVALID_MESSAGE, markdown=False)
        return {"status": "ok"}

    await queue.enqueue(queue_msg)
    await gateway.send_message(chat_id, messages.PROCESSING, markdown=False)
    return {"status": "ok"}
