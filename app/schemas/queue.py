"""Queue message schemas for async processing."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

MessageType = Literal["document", "photo", "text"]


class ChatInfo(BaseModel):
    """Telegram chat information.

    Attributes:
        id: Unique chat identifier.
        type: Chat type (private, group, supergroup, channel).
    """

    id: int
    type: str


class MessageInfo(BaseModel):
    """Telegram message information.

    Attributes:
        id: Unique message identifier within the chat.
        text: Text body or caption of the message.
    """

    id: int
    text: str | None = None


class UserInfo(BaseModel):
    """Telegram user information.

    Attributes:
        telegram_id: Unique Telegram user identifier.
        first_name: User's first name.
        username: User's Telegram username.
    """

    telegram_id: int
    first_name: str | None = None
    username: str | None = None


class FileInfo(BaseModel):
    """Telegram file information for downloading.

    Attributes:
        file_id: Telegram file identifier for downloading.
        file_unique_id: Unique file identifier across bots.
        file_name: Original filename.
        mime_type: MIME type of the file.
        file_size: File size in bytes.
    """

    file_id: str
    file_unique_id: str
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class QueueMessage(BaseModel):
    """Message structure for async processing queue.

    Attributes:
        id: Unique queue message identifier (UUID).
        timestamp: When the message was received.
        type: Message type (document, photo, text).
        chat: Chat information for replies.
        message: Message information including reply ID.
        user: User who sent the message.
        file: File information if present.
    """

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: MessageType
    chat: ChatInfo
    message: MessageInfo
    user: UserInfo
    file: FileInfo | None = None

    def to_json(self) -> str:
        """Serialize the message to JSON string.

        Returns:
            JSON string representation.
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "QueueMessage":
        """Deserialize a JSON string to QueueMessage.

        Args:
            data: JSON string.

        Returns:
            QueueMessage instance.
        """
        return cls.model_validate_json(data)
