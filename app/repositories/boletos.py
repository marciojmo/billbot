"""Boleto data access."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Boleto, User


class BoletoRepository:
    """Queries and persists boletos within a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a session.

        Args:
            session: The session to run queries on.
        """
        self._session = session

    async def add(self, boleto: Boleto) -> None:
        """Insert a boleto and commit.

        Args:
            boleto: The boleto to insert.

        Raises:
            IntegrityError: If the barcode already exists.
        """
        self._session.add(boleto)
        await self._session.commit()

    async def list_by_telegram_id(self, telegram_id: int) -> Sequence[Boleto]:
        """List a user's boletos, newest first.

        Args:
            telegram_id: The Telegram user ID.

        Returns:
            The user's boletos.
        """
        result = await self._session.execute(
            select(Boleto)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .order_by(Boleto.created_at.desc())
        )
        return result.scalars().all()
