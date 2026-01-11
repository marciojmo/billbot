"""Database storage for boleto data."""

import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Boleto, User
from app.db.session import get_session
from app.schemas.ocr import BoletoData

logger = logging.getLogger(__name__)


def parse_value_to_cents(value_str: str | None) -> int | None:
    """Parse a Brazilian currency string to cents.

    Args:
        value_str: Value string like "199,00" or "1.234,56".

    Returns:
        Value in cents (19900) or None if parsing fails.
    """
    if not value_str:
        return None

    try:
        cleaned = re.sub(r"[^\d,]", "", value_str)
        cleaned = cleaned.replace(",", ".")
        return int(float(cleaned) * 100)
    except (ValueError, AttributeError):
        return None


def parse_due_date(date_str: str | None) -> datetime | None:
    """Parse a Brazilian date string to datetime.

    Args:
        date_str: Date string like "15/01/2026".

    Returns:
        Datetime object or None if parsing fails.
    """
    if not date_str:
        return None

    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


async def get_or_create_user(
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> User:
    """Get or create a user by Telegram ID.

    Args:
        telegram_id: The Telegram user ID.
        first_name: User's first name.
        username: User's Telegram username.

    Returns:
        The User model instance.
    """
    session = await get_session()
    try:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    finally:
        await session.close()


async def store_boleto(
    data: BoletoData,
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> bool:
    """Store boleto data in the database.

    Args:
        data: The extracted boleto data.
        telegram_id: The Telegram user ID.
        first_name: User's first name.
        username: User's Telegram username.

    Returns:
        True if stored successfully, False if duplicate barcode.
    """
    if not data.barcode:
        logger.warning("Cannot store boleto without barcode")
        return False

    user = await get_or_create_user(telegram_id, first_name, username)

    session = await get_session()
    try:
        boleto = Boleto(
            user_id=user.id,
            barcode=data.barcode,
            due_date=parse_due_date(data.due_date),
            due_date_raw=data.due_date,
            value_cents=parse_value_to_cents(data.value),
            value_raw=data.value,
            issuer=data.issuer,
            confidence=data.confidence,
            raw_text=data.raw_text,
        )
        session.add(boleto)
        await session.commit()
        logger.info(f"Stored boleto: {data.barcode}")
        return True
    except IntegrityError:
        await session.rollback()
        logger.info(f"Duplicate boleto ignored: {data.barcode}")
        return False
    finally:
        await session.close()


async def get_user_boletos(telegram_id: int) -> list[dict]:
    """Get all boletos for a user.

    Args:
        telegram_id: The Telegram user ID.

    Returns:
        List of boleto data dicts.
    """
    session = await get_session()
    try:
        result = await session.execute(
            select(Boleto)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .order_by(Boleto.created_at.desc())
        )
        boletos = result.scalars().all()

        return [
            {
                "barcode": b.barcode,
                "due_date": b.due_date_raw,
                "value": b.value_raw,
                "issuer": b.issuer,
                "confidence": b.confidence,
                "status": b.status,
            }
            for b in boletos
        ]
    finally:
        await session.close()
