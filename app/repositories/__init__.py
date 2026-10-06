"""Data access repositories."""

from app.repositories.boletos import BoletoRepository
from app.repositories.users import UserRepository

__all__ = ["BoletoRepository", "UserRepository"]
