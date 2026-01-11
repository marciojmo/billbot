"""Database models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class User(Base):
    """Telegram user model.

    Attributes:
        id: Primary key.
        telegram_id: Unique Telegram user ID.
        first_name: User's first name.
        username: User's Telegram username.
        created_at: Timestamp when the user was created.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    boletos: Mapped[list["Boleto"]] = relationship("Boleto", back_populates="user")


class Boleto(Base):
    """Boleto payment slip model.

    Attributes:
        id: Primary key.
        user_id: Foreign key to the user who sent the boleto.
        barcode: The barcode number (linha digitável).
        due_date: Parsed due date.
        due_date_raw: Original due date string from OCR.
        value_cents: Value in cents (19900 = R$ 199,00).
        value_raw: Original value string from OCR.
        issuer: Company/issuer name.
        confidence: OCR confidence level (0.0 to 1.0).
        raw_text: Additional OCR notes.
        status: Payment status (pending, paid, expired).
        created_at: Timestamp when the boleto was created.
        paid_at: Timestamp when the boleto was marked as paid.
    """

    __tablename__ = "boletos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    barcode: Mapped[str | None] = mapped_column(String(60), unique=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    due_date_raw: Mapped[str | None] = mapped_column(String(20))
    value_cents: Mapped[int | None] = mapped_column(Integer)
    value_raw: Mapped[str | None] = mapped_column(String(20))
    issuer: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float | None] = mapped_column(Float)
    raw_text: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship("User", back_populates="boletos")
