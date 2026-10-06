"""Boleto business logic."""

import logging

from sqlalchemy.exc import IntegrityError

from app.db.database import Database
from app.db.models import Boleto
from app.repositories.boletos import BoletoRepository
from app.repositories.users import UserRepository
from app.schemas.boleto import BoletoData, StoredBoleto
from app.schemas.queue import UserInfo
from app.services.parsing import parse_due_date, parse_value_to_cents

logger = logging.getLogger(__name__)


class BoletoService:
    """Stores extracted boletos and lists a user's boletos."""

    def __init__(self, database: Database) -> None:
        """Create the service.

        Args:
            database: The database to open sessions on.
        """
        self._database = database

    async def store(self, data: BoletoData, user: UserInfo) -> bool:
        """Store extracted boleto data for a user.

        The user is created on first use. Boletos without a barcode are
        skipped, and a barcode that already exists is ignored.

        Args:
            data: The extracted boleto data.
            user: The Telegram user who sent the boleto.

        Returns:
            True if stored, False if skipped or a duplicate.
        """
        if not data.barcode:
            logger.warning("Cannot store boleto without barcode")
            return False

        async with self._database.session() as session:
            db_user = await UserRepository(session).get_or_create(
                user.telegram_id, user.first_name, user.username
            )
            boleto = Boleto(
                user_id=db_user.id,
                barcode=data.barcode,
                due_date=parse_due_date(data.due_date),
                due_date_raw=data.due_date,
                value_cents=parse_value_to_cents(data.value),
                value_raw=data.value,
                issuer=data.issuer,
                confidence=data.confidence,
                raw_text=data.raw_text,
            )
            try:
                await BoletoRepository(session).add(boleto)
            except IntegrityError:
                await session.rollback()
                logger.info("Duplicate boleto ignored: %s", data.barcode)
                return False

        logger.info("Stored boleto: %s", data.barcode)
        return True

    async def list_for_user(self, telegram_id: int) -> list[StoredBoleto]:
        """List a user's boletos, newest first.

        Args:
            telegram_id: The Telegram user ID.

        Returns:
            The user's stored boletos.
        """
        async with self._database.session() as session:
            boletos = await BoletoRepository(session).list_by_telegram_id(telegram_id)

        return [
            StoredBoleto(
                barcode=b.barcode,
                due_date=b.due_date_raw,
                value=b.value_raw,
                issuer=b.issuer,
                confidence=b.confidence,
                status=b.status,
            )
            for b in boletos
        ]
