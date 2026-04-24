from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select

from src.models.offer_reservation import OfferReservation, OfferReservationStatus
from src.repositories.base import BaseRepository


class OfferReservationRepository(BaseRepository[OfferReservation]):
  model = OfferReservation

  async def create_pending(
    self,
    *,
    reservation_id: str,
    offer_id: int,
    quantity: int,
    reservation_owner: int,
    expires_at: datetime,
  ) -> OfferReservation:
    reservation = OfferReservation(
      reservation_id=reservation_id,
      offer_id=offer_id,
      quantity=quantity,
      reservation_owner=reservation_owner,
      status=OfferReservationStatus.PENDING,
      expires_at=expires_at,
    )
    self.session.add(reservation)
    await self.session.flush()
    await self.session.refresh(reservation)
    return reservation

  async def get_by_reservation_id(
    self,
    reservation_id: str,
    *,
    for_update: bool = False,
  ) -> OfferReservation | None:
    stmt = select(OfferReservation).where(OfferReservation.reservation_id == reservation_id)
    if for_update:
      stmt = stmt.with_for_update()
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_active_pending_quantities(self, offer_ids: list[int]) -> dict[int, int]:
    if not offer_ids:
      return {}
    now = datetime.now(UTC)
    stmt = (
      select(OfferReservation.offer_id, func.coalesce(func.sum(OfferReservation.quantity), 0))
      .where(
        OfferReservation.offer_id.in_(offer_ids),
        OfferReservation.status == OfferReservationStatus.PENDING,
        OfferReservation.expires_at > now,
      )
      .group_by(OfferReservation.offer_id)
    )
    result = await self.session.execute(stmt)
    return {int(offer_id): int(quantity) for offer_id, quantity in result.all()}

  async def mark_expired_if_needed(self, reservation: OfferReservation) -> OfferReservation:
    if (
      reservation.status == OfferReservationStatus.PENDING
      and reservation.expires_at <= datetime.now(UTC)
    ):
      reservation.status = OfferReservationStatus.EXPIRED
      await self.session.flush()
    return reservation

  async def set_status(
    self,
    reservation: OfferReservation,
    status: OfferReservationStatus,
  ) -> OfferReservation:
    reservation.status = status
    await self.session.flush()
    await self.session.refresh(reservation)
    return reservation
