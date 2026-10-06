"""Conversion of Telegram messages into queue messages."""

import logging

from telegram import Message

from app.schemas.queue import (
    ChatInfo,
    FileInfo,
    MessageInfo,
    MessageType,
    QueueMessage,
    UserInfo,
)

logger = logging.getLogger(__name__)


def to_queue_message(message: Message) -> QueueMessage | None:
    """Create a QueueMessage from a Telegram Message.

    Args:
        message: The Telegram message.

    Returns:
        QueueMessage instance, or None if message is invalid.
    """
    if not message.from_user:
        logger.warning("Message %s has no user info", message.message_id)
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
    msg_type: MessageType = "text"

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
