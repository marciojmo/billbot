"""Telegram update and message schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class TelegramUpdate(BaseModel):
    """Raw Telegram update for FastAPI request validation.

    This model accepts the raw JSON payload from Telegram's webhook.
    The actual parsing is done by python-telegram-bot library.

    Attributes:
        update_id: Unique update identifier.
    """

    model_config = ConfigDict(extra="allow")

    update_id: int

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary for telegram library parsing.

        Returns:
            The update data as a dictionary.
        """
        return self.model_dump()
