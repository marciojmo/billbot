"""python-telegram-bot update handlers."""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.bot import messages
from app.bot.mapper import to_queue_message
from app.worker.queue import MessageQueue

QUEUE_KEY = "queue"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greet the user. Used for /start and any non-file message.

    Args:
        update: The Telegram update.
        context: The callback context.
    """
    if not update.message:
        return
    user = update.message.from_user
    await update.message.reply_text(messages.format_start(user.first_name if user else None))


async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enqueue document and photo messages for processing.

    Args:
        update: The Telegram update.
        context: The callback context; its ``bot_data`` holds the queue.
    """
    if not update.message:
        return

    queue_msg = to_queue_message(update.message)
    if not queue_msg:
        await update.message.reply_text(messages.INVALID_MESSAGE)
        return

    queue: MessageQueue = context.bot_data[QUEUE_KEY]
    await queue.enqueue(queue_msg)
    await update.message.reply_text(messages.PROCESSING)


def register_handlers(application: Application, queue: MessageQueue) -> None:
    """Register all bot handlers and make the queue available to them.

    Args:
        application: The python-telegram-bot application.
        queue: The queue file messages are sent to.
    """
    application.bot_data[QUEUE_KEY] = queue
    files = filters.Document.ALL | filters.PHOTO
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(files, file_handler))
    application.add_handler(MessageHandler(~files, start_handler))
