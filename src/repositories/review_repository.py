from __future__ import annotations

from sqlalchemy import func, select

from src.models.review import Review
from src.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
  model = Review

  async def list_filtered(
    self,
    *,
    venue_id: int | None,
    user_id: int | None,
    offset: int,
    limit: int,
  ) -> list[Review]:
    stmt = self._base_query().offset(offset).limit(limit)
    if venue_id is not None:
      stmt = stmt.where(Review.venue_id == venue_id)
    if user_id is not None:
      stmt = stmt.where(Review.user_id == user_id)
    result = await self.session.execute(stmt)
    return list(result.scalars().all())

  async def count_filtered(self, *, venue_id: int | None, user_id: int | None) -> int:
    stmt = select(func.count(Review.id)).where(Review.deleted_at.is_(None))
    if venue_id is not None:
      stmt = stmt.where(Review.venue_id == venue_id)
    if user_id is not None:
      stmt = stmt.where(Review.user_id == user_id)
    result = await self.session.execute(stmt)
    return int(result.scalar_one())

  async def list_by_venue(
    self,
    venue_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Review]:
    return await self.list_filtered(venue_id=venue_id, user_id=None, offset=offset, limit=limit)

  async def get_by_order(self, order_id: int) -> Review | None:
    stmt = self._base_query().where(Review.order_id == order_id)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
