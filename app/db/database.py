"""Database engine and session management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base


class Database:
    """Owns the async engine and hands out sessions.

    Attributes:
        engine: The SQLAlchemy async engine.
    """

    def __init__(self, url: str, echo: bool = False) -> None:
        """Create the engine and session factory.

        Args:
            url: The database connection URL.
            echo: Whether to log emitted SQL.
        """
        self.engine: AsyncEngine = create_async_engine(url, echo=echo)
        self._sessionmaker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self) -> None:
        """Create all tables that do not exist yet."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Open a session that is closed when the block exits.

        Yields:
            An async database session.
        """
        async with self._sessionmaker() as session:
            yield session

    async def dispose(self) -> None:
        """Close all pooled connections."""
        await self.engine.dispose()
