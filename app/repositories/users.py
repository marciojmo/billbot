"""User data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    """Queries and persists users within a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a session.

        Args:
            session: The session to run queries on.
        """
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Find a user by Telegram ID.

        Args:
            telegram_id: The Telegram user ID.

        Returns:
            The user, or None if not found.
        """
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str | None = None,
        username: str | None = None,
    ) -> User:
        """Get a user by Telegram ID, creating and committing it if missing.

        Args:
            telegram_id: The Telegram user ID.
            first_name: User's first name.
            username: User's Telegram username.

        Returns:
            The existing or newly created user.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user

        user = User(telegram_id=telegram_id, first_name=first_name, username=username)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
