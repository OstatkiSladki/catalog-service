from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from src.api.deps import IdentityContext
from src.models.offer import Offer, OfferStatus
from src.repositories.offer_repository import OfferRepository
from src.schemas.offer import OfferCreate, OfferUpdate


class OfferValidationError(ValueError):
  pass


class OfferForbiddenError(PermissionError):
  pass


class OfferService:
  def __init__(self, repository: OfferRepository) -> None:
    self.repository = repository

  async def get_by_id(self, offer_id: int) -> Offer | None:
    return await self.repository.get_by_id(offer_id)

  async def list(
    self,
    *,
    venue_id: int | None,
    status: OfferStatus | None,
    category_id: int | None,
    offset: int,
    limit: int,
  ) -> tuple[list[Offer], int]:
    items = await self.repository.list_filtered(
      venue_id=venue_id,
      status=status,
      category_id=category_id,
      offset=offset,
      limit=limit,
    )
    total_count = await self.repository.count_filtered(
      venue_id=venue_id,
      status=status,
      category_id=category_id,
    )
    return items, total_count

  async def create(self, payload: OfferCreate, identity: IdentityContext) -> Offer:
    self._ensure_can_manage_venue(identity, payload.venue_id)
    self._validate_prices(payload.current_price, payload.original_price)
    self._validate_expiration(payload.expires_at)
    data = payload.model_dump()
    items = data.pop("items")
    return await self.repository.create_with_items(data, items)

  async def update(
    self,
    offer_id: int,
    payload: OfferUpdate,
    identity: IdentityContext,
  ) -> Offer | None:
    existing = await self.repository.get_by_id(offer_id)
    if existing is None:
      return None
    self._ensure_can_manage_venue(identity, existing.venue_id)
    current_price = payload.current_price or existing.current_price
    original_price = payload.original_price or existing.original_price
    self._validate_prices(current_price, original_price)
    if payload.expires_at is not None:
      self._validate_expiration(payload.expires_at)
    data = payload.model_dump(exclude_unset=True)
    items = data.pop("items", None)
    return await self.repository.update_with_items(offer_id, data, items)

  async def cancel(self, offer_id: int, identity: IdentityContext) -> bool:
    existing = await self.repository.get_by_id(offer_id)
    if existing is None:
      return False
    self._ensure_can_manage_venue(identity, existing.venue_id)
    updated = await self.repository.update(offer_id, {"status": OfferStatus.CANCELLED})
    return updated is not None

  def _validate_prices(self, current_price: Decimal, original_price: Decimal) -> None:
    if current_price >= original_price:
      raise OfferValidationError("Current price must be lower than original price")

  def _validate_expiration(self, expires_at: datetime) -> None:
    if expires_at <= datetime.now(UTC):
      raise OfferValidationError("Offer expiration must be in the future")

  def _ensure_can_manage_venue(self, identity: IdentityContext, venue_id: int) -> None:
    if identity.user_role == "admin":
      return
    if identity.user_role != "staff":
      raise OfferForbiddenError("Only staff or admin can manage offers")
    if identity.user_venue_id != venue_id:
      raise OfferForbiddenError("Staff can manage offers only for their own venue")
