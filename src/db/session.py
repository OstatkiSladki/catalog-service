from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import Settings


class DatabaseSessionManager:
    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._engine = engine
        self._session_factory = session_factory

    @classmethod
    def from_settings(cls, settings: Settings) -> DatabaseSessionManager:
        engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            future=True,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        return cls(engine=engine, session_factory=session_factory)

    async def healthcheck(self) -> bool:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            yield session

    async def close(self) -> None:
        await self._engine.dispose()
