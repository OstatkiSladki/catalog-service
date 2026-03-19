from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from src.models.offer import Offer, OfferStatus
from src.models.offer_item import OfferItem
from src.models.product_category import ProductCategory
from src.repositories.base import BaseRepository


class OfferRepository(BaseRepository[Offer]):
  model = Offer

  async def get_by_id(self, object_id: int) -> Offer | None:
    stmt = select(Offer).options(selectinload(Offer.items)).where(Offer.id == object_id)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

  async def list_filtered(
    self,
    *,
    venue_id: int | None,
    status: OfferStatus | None,
    category_id: int | None,
    offset: int,
    limit: int,
  ) -> list[Offer]:
    now = datetime.now(UTC)
    stmt = select(Offer).options(selectinload(Offer.items))
    if venue_id is not None:
      stmt = stmt.where(Offer.venue_id == venue_id)
    if status is None:
      stmt = stmt.where(Offer.status == OfferStatus.ACTIVE).where(Offer.expires_at > now)
    else:
      stmt = stmt.where(Offer.status == status)
      if status == OfferStatus.ACTIVE:
        stmt = stmt.where(Offer.expires_at > now)
    if category_id is not None:
      stmt = stmt.join(OfferItem, OfferItem.offer_id == Offer.id).join(
        ProductCategory,
        ProductCategory.product_id == OfferItem.product_id,
      )
      stmt = stmt.where(ProductCategory.category_id == category_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await self.session.execute(stmt)
    return list(result.scalars().unique().all())

  async def count_filtered(
    self,
    *,
    venue_id: int | None,
    status: OfferStatus | None,
    category_id: int | None,
  ) -> int:
    now = datetime.now(UTC)
    stmt = select(func.count(func.distinct(Offer.id)))
    if venue_id is not None:
      stmt = stmt.where(Offer.venue_id == venue_id)
    if status is None:
      stmt = stmt.where(Offer.status == OfferStatus.ACTIVE).where(Offer.expires_at > now)
    else:
      stmt = stmt.where(Offer.status == status)
      if status == OfferStatus.ACTIVE:
        stmt = stmt.where(Offer.expires_at > now)
    if category_id is not None:
      stmt = stmt.join(OfferItem, OfferItem.offer_id == Offer.id).join(
        ProductCategory,
        ProductCategory.product_id == OfferItem.product_id,
      )
      stmt = stmt.where(ProductCategory.category_id == category_id)
    result = await self.session.execute(stmt)
    return int(result.scalar_one())

  async def create_with_items(
    self,
    data: dict[str, object],
    items: Sequence[dict[str, object]],
  ) -> Offer:
    offer = Offer(**data)
    offer.items = [self._build_offer_item(item) for item in items]
    self.session.add(offer)
    return offer

  async def update_with_items(
    self,
    offer_id: int,
    data: dict[str, object],
    items: Sequence[dict[str, object]] | None,
  ) -> Offer | None:
    updated = await self.update(offer_id, data)
    if updated is None:
      return None
    if items is not None:
      await self._replace_items(offer_id, items)
    return await self.get_by_id(offer_id)

  async def list_by_venue(
    self,
    venue_id: int,
    status: OfferStatus | None = None,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Offer]:
    return await self.list_filtered(
      venue_id=venue_id,
      status=status,
      category_id=None,
      offset=offset,
      limit=limit,
    )

  async def get_active_offers(self, *, offset: int = 0, limit: int = 20) -> list[Offer]:
    return await self.list_filtered(
      venue_id=None,
      status=None,
      category_id=None,
      offset=offset,
      limit=limit,
    )

  async def _replace_items(self, offer_id: int, items: Sequence[dict[str, object]]) -> None:
    await self.session.execute(delete(OfferItem).where(OfferItem.offer_id == offer_id))
    for item in items:
      self.session.add(self._build_offer_item(item, offer_id=offer_id))

  def _build_offer_item(self, item: dict[str, object], *, offer_id: int | None = None) -> OfferItem:
    product_id = item.get("product_id")
    quantity = item.get("quantity", 1)
    if not isinstance(product_id, int) or not isinstance(quantity, int):
      raise ValueError("Invalid offer item")
    if offer_id is None:
      return OfferItem(product_id=product_id, quantity=quantity)
    return OfferItem(offer_id=offer_id, product_id=product_id, quantity=quantity)
