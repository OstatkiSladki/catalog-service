from __future__ import annotations

from datetime import UTC, datetime

from src.models.offer import Offer, OfferStatus
from src.repositories.base import BaseRepository


class OfferRepository(BaseRepository[Offer]):
  model = Offer

  async def list_by_venue(
    self,
    venue_id: int,
    status: OfferStatus | None = None,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Offer]:
    stmt = self._base_query().where(Offer.venue_id == venue_id).offset(offset).limit(limit)
    if status is not None:
      stmt = stmt.where(Offer.status == status)
    result = await self.session.execute(stmt)
    return list(result.scalars().all())

  async def get_active_offers(self, *, offset: int = 0, limit: int = 20) -> list[Offer]:
    now = datetime.now(UTC)
    stmt = (
      self._base_query()
      .where(Offer.status == OfferStatus.ACTIVE)
      .where(Offer.expires_at > now)
      .offset(offset)
      .limit(limit)
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
