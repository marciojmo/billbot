"""Message queue service for async processing."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Message

from app.schemas.queue import (
    ChatInfo,
    FileInfo,
    MessageInfo,
    QueueMessage,
    UserInfo,
)

logger = logging.getLogger(__name__)

MessageHandler = Callable[[QueueMessage], Coroutine[Any, Any, None]]

_queue: asyncio.Queue[QueueMessage] = asyncio.Queue()
_handlers: list[MessageHandler] = []


def create_queue_message(message: Message) -> QueueMessage | None:
    """Create a QueueMessage from a Telegram Message.

    Args:
        message: The Telegram message.

    Returns:
        QueueMessage instance, or None if message is invalid.
    """
    if not message.from_user:
        logger.warning(f"Message {message.message_id} has no user info")
        return None

    user = UserInfo(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )

    chat = ChatInfo(
        id=message.chat.id,
        type=message.chat.type,
    )

    msg_info = MessageInfo(
        id=message.message_id,
        text=message.text or message.caption,
    )

    file_info: FileInfo | None = None
    msg_type: str = "text"

    if message.document:
        msg_type = "document"
        file_info = FileInfo(
            file_id=message.document.file_id,
            file_unique_id=message.document.file_unique_id,
            file_name=message.document.file_name,
            mime_type=message.document.mime_type,
            file_size=message.document.file_size,
        )
    elif message.photo:
        msg_type = "photo"
        photo = message.photo[-1]
        file_info = FileInfo(
            file_id=photo.file_id,
            file_unique_id=photo.file_unique_id,
            file_name=None,
            mime_type="image/jpeg",
            file_size=photo.file_size,
        )

    return QueueMessage(
        type=msg_type,
        chat=chat,
        message=msg_info,
        user=user,
        file=file_info,
    )


async def enqueue(message: QueueMessage) -> None:
    """Add a message to the processing queue.

    Args:
        message: The queue message to enqueue.
    """
    await _queue.put(message)
    logger.info(f"Enqueued message {message.id} (type: {message.type})")


def register_handler(handler: MessageHandler) -> None:
    """Register a handler for processing queue messages.

    Args:
        handler: Async function that processes QueueMessage.
    """
    _handlers.append(handler)
    logger.info(f"Registered handler: {handler.__name__}")


async def process_queue() -> None:
    """Process messages from the queue indefinitely.

    Runs all registered handlers for each message.
    """
    logger.info(f"Queue processor started with {len(_handlers)} handlers")

    while True:
        message = await _queue.get()
        logger.info(f"Processing message {message.id}")

        for handler in _handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}")

        _queue.task_done()


async def start_queue_processor() -> asyncio.Task[None]:
    """Start the queue processor as a background task.

    Returns:
        The asyncio task running the processor.
    """
    return asyncio.create_task(process_queue())


def get_queue_size() -> int:
    """Get the current number of messages in the queue.

    Returns:
        Number of pending messages.
    """
    return _queue.qsize()
