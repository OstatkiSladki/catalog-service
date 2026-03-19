from __future__ import annotations

from src.models.review import Review
from src.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
  model = Review

  async def list_by_venue(
    self,
    venue_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Review]:
    return await self.list(filters={"venue_id": venue_id}, offset=offset, limit=limit)

  async def get_by_order(self, order_id: int) -> Review | None:
    stmt = self._base_query().where(Review.order_id == order_id)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
