"""Telegram bot polling mode for local development."""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.config import settings
from app.db import init_db
from app.services.command_handler import get_start_message
from app.services.consumers import logger_consumer, ocr_consumer, send_reply
from app.services.message_handler import get_user_boletos_response
from app.services.queue import (
    create_queue_message,
    enqueue,
    register_handler,
    start_queue_processor,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /start command.

    Args:
        update: The Telegram update containing the command.
        context: The callback context.
    """
    if update.message and update.message.from_user:
        name = update.message.from_user.first_name
        await update.message.reply_text(get_start_message(name))


async def file_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle incoming document and photo messages.

    Args:
        update: The Telegram update containing the message.
        context: The callback context.
    """
    if not update.message:
        return

    queue_msg = create_queue_message(update.message)
    if not queue_msg:
        await update.message.reply_text(
            "Não consegui processar essa mensagem. Pode tentar novamente?"
        )
        return

    await enqueue(queue_msg)
    await update.message.reply_text(
        "🔄 Processndo mensagem.. Já aviso quando estiver pronto! 😉"
    )


async def fallback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle any message that doesn't contain a file or photo.

    Args:
        update: The Telegram update containing the message.
        context: The callback context.
    """
    if update.message and update.message.from_user:
        name = update.message.from_user.first_name
        await update.message.reply_text(get_start_message(name))


async def response_consumer(msg) -> None:
    """Consumer that sends the final response to the user.

    Args:
        msg: The queue message.
    """
    if msg.type == "text":
        return

    response = await get_user_boletos_response(msg.user.telegram_id)
    await send_reply(msg.chat.id, response, msg.message.id)


async def run_bot() -> None:
    """Initialize database, queue, and run the bot."""
    await init_db()
    logger.info("Database initialized")

    register_handler(logger_consumer)
    register_handler(ocr_consumer)
    register_handler(response_consumer)

    await start_queue_processor()
    logger.info("Queue processor started")

    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.PHOTO, file_handler))
    app.add_handler(
        MessageHandler(~filters.Document.ALL & ~filters.PHOTO, fallback_handler)
    )

    logger.info("Starting bot in polling mode...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> None:
    """Run the bot in polling mode."""
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        raise SystemExit(1)

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
