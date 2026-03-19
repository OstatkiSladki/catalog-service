from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
  model: type[ModelType]

  def __init__(self, session: AsyncSession) -> None:
    self.session = session

  def _base_query(self) -> Select[tuple[ModelType]]:
    stmt = select(self.model)
    if hasattr(self.model, "deleted_at"):
      stmt = stmt.where(getattr(self.model, "deleted_at").is_(None))  # noqa: B009
    return stmt

  async def get_by_id(self, object_id: int) -> ModelType | None:
    stmt = self._base_query().where(getattr(self.model, "id") == object_id)  # noqa: B009
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

  async def list(
    self,
    *,
    filters: dict[str, Any] | None = None,
    offset: int = 0,
    limit: int = 20,
  ) -> list[ModelType]:
    stmt = self._base_query().offset(offset).limit(limit)
    if filters:
      for key, value in filters.items():
        stmt = stmt.where(getattr(self.model, key) == value)
    result = await self.session.execute(stmt)
    return list(result.scalars().all())

  async def count(self, *, filters: dict[str, Any] | None = None) -> int:
    stmt = select(func.count(getattr(self.model, "id")))  # noqa: B009
    if hasattr(self.model, "deleted_at"):
      stmt = stmt.where(getattr(self.model, "deleted_at").is_(None))  # noqa: B009
    if filters:
      for key, value in filters.items():
        stmt = stmt.where(getattr(self.model, key) == value)
    result = await self.session.execute(stmt)
    return int(result.scalar_one())

  async def create(self, data: dict[str, Any]) -> ModelType:
    item = self.model(**data)
    self.session.add(item)
    return item

  async def update(self, object_id: int, data: dict[str, Any]) -> ModelType | None:
    stmt = update(self.model).where(getattr(self.model, "id") == object_id).values(**data)  # noqa: B009
    await self.session.execute(stmt)
    return await self.get_by_id(object_id)

  async def soft_delete(self, object_id: int) -> bool:
    if not hasattr(self.model, "deleted_at"):
      raise ValueError(f"{self.model.__name__} does not support soft-delete")
    stmt = (
      update(self.model)
      .where(getattr(self.model, "id") == object_id)  # noqa: B009
      .values(deleted_at=datetime.now(UTC))
    )
    result = await self.session.execute(stmt)
    await self.session.flush()
    return bool(getattr(result, "rowcount", 0) > 0)

  async def hard_delete(self, object_id: int) -> bool:
    stmt = delete(self.model).where(getattr(self.model, "id") == object_id)  # noqa: B009
    result = await self.session.execute(stmt)
    await self.session.flush()
    return bool(getattr(result, "rowcount", 0) > 0)
