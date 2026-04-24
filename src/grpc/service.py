from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from google.protobuf.timestamp_pb2 import Timestamp

import grpc
from src.db.session import DatabaseSessionManager
from src.grpc.generated import catalog_inventory_pb2, catalog_inventory_pb2_grpc
from src.models.offer import OfferStatus
from src.models.offer_reservation import OfferReservationStatus
from src.repositories.offer_repository import OfferRepository
from src.repositories.offer_reservation_repository import OfferReservationRepository

_RESERVATION_TTL = timedelta(minutes=15)


class CatalogInventoryGrpcService(catalog_inventory_pb2_grpc.CatalogInventoryServiceServicer):
  def __init__(self, session_manager: DatabaseSessionManager) -> None:
    self._session_manager = session_manager

  async def CheckAvailability(
    self,
    request: catalog_inventory_pb2.CheckAvailabilityRequest,
    context: grpc.aio.ServicerContext,
  ) -> catalog_inventory_pb2.CheckAvailabilityResponse:
    offer_ids = [int(offer_id) for offer_id in request.offer_ids]
    async with self._session_manager.session_context() as session:
      offer_repo = OfferRepository(session)
      reservation_repo = OfferReservationRepository(session)

      offers = await offer_repo.get_by_ids(offer_ids)
      pending_map = await reservation_repo.get_active_pending_quantities(offer_ids)
      quantities = {
        int(offer.id): max(int(offer.quantity_available) - pending_map.get(int(offer.id), 0), 0)
        for offer in offers
      }
      all_found = len(offers) == len(set(offer_ids))
      all_available = all_found and all(quantity > 0 for quantity in quantities.values())
      return catalog_inventory_pb2.CheckAvailabilityResponse(
        available=all_available,
        quantities=quantities,
      )

  async def GetOfferSnapshot(
    self,
    request: catalog_inventory_pb2.GetOfferSnapshotRequest,
    context: grpc.aio.ServicerContext,
  ) -> catalog_inventory_pb2.GetOfferSnapshotResponse:
    async with self._session_manager.session_context() as session:
      offer = await OfferRepository(session).get_by_id(int(request.offer_id))
      if offer is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "Offer not found")
      if not offer.items:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Offer has no items")

      product = offer.items[0].product
      product_name = product.name if product is not None else f"Offer {offer.id}"
      is_active = (
        offer.status == OfferStatus.ACTIVE
        and offer.expires_at > datetime.now(UTC)
        and int(offer.quantity_available) > 0
      )
      return catalog_inventory_pb2.GetOfferSnapshotResponse(
        offer_id=int(offer.id),
        venue_id=int(offer.venue_id),
        product_name=str(product_name),
        price=f"{Decimal(str(offer.current_price)):.2f}",
        is_active=is_active,
      )

  async def ReserveItems(
    self,
    request: catalog_inventory_pb2.ReserveItemsRequest,
    context: grpc.aio.ServicerContext,
  ) -> catalog_inventory_pb2.ReserveItemsResponse:
    if request.quantity <= 0:
      await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "quantity must be positive")

    async with self._session_manager.session_context() as session:
      offer_repo = OfferRepository(session)
      reservation_repo = OfferReservationRepository(session)

      offer = await offer_repo.get_by_id_for_update(int(request.offer_id))
      if offer is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "Offer not found")

      pending_map = await reservation_repo.get_active_pending_quantities([int(request.offer_id)])
      effective_available = int(offer.quantity_available) - pending_map.get(
        int(request.offer_id),
        0,
      )
      if effective_available < int(request.quantity):
        await context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Insufficient quantity")

      expires_at = datetime.now(UTC) + _RESERVATION_TTL
      reservation = await reservation_repo.create_pending(
        reservation_id=uuid4().hex,
        offer_id=int(request.offer_id),
        quantity=int(request.quantity),
        reservation_owner=int(request.reservation_owner),
        expires_at=expires_at,
      )

      timestamp = Timestamp()
      timestamp.FromDatetime(expires_at)
      return catalog_inventory_pb2.ReserveItemsResponse(
        reservation_id=reservation.reservation_id,
        expires_at=timestamp,
      )

  async def ConfirmReservation(
    self,
    request: catalog_inventory_pb2.ConfirmReservationRequest,
    context: grpc.aio.ServicerContext,
  ) -> catalog_inventory_pb2.ConfirmReservationResponse:
    async with self._session_manager.session_context() as session:
      offer_repo = OfferRepository(session)
      reservation_repo = OfferReservationRepository(session)

      reservation = await reservation_repo.get_by_reservation_id(
        request.reservation_id,
        for_update=True,
      )
      if reservation is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "Reservation not found")

      await reservation_repo.mark_expired_if_needed(reservation)
      if reservation.status != OfferReservationStatus.PENDING:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Reservation is not pending")

      offer = await offer_repo.get_by_id_for_update(int(reservation.offer_id))
      if offer is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "Offer not found")

      if int(offer.quantity_available) < int(reservation.quantity):
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Offer quantity changed")

      offer.quantity_available -= reservation.quantity
      await reservation_repo.set_status(reservation, OfferReservationStatus.CONFIRMED)
      await session.flush()
      return catalog_inventory_pb2.ConfirmReservationResponse(success=True)

  async def CancelReservation(
    self,
    request: catalog_inventory_pb2.CancelReservationRequest,
    context: grpc.aio.ServicerContext,
  ) -> catalog_inventory_pb2.CancelReservationResponse:
    async with self._session_manager.session_context() as session:
      reservation_repo = OfferReservationRepository(session)
      reservation = await reservation_repo.get_by_reservation_id(
        request.reservation_id,
        for_update=True,
      )
      if reservation is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "Reservation not found")

      await reservation_repo.mark_expired_if_needed(reservation)
      if reservation.status == OfferReservationStatus.PENDING:
        await reservation_repo.set_status(reservation, OfferReservationStatus.CANCELLED)
        return catalog_inventory_pb2.CancelReservationResponse(success=True)
      return catalog_inventory_pb2.CancelReservationResponse(success=False)
