from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime

from src.models.base import Base, TimestampCreatedMixin


class OfferReservationStatus(StrEnum):
  PENDING = "pending"
  CONFIRMED = "confirmed"
  CANCELLED = "cancelled"
  EXPIRED = "expired"


class OfferReservation(Base, TimestampCreatedMixin):
  __tablename__ = "offer_reservations"

  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  reservation_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
  offer_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey("offers.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  quantity: Mapped[int] = mapped_column(Integer, nullable=False)
  reservation_owner: Mapped[int] = mapped_column(BigInteger, nullable=False)
  status: Mapped[OfferReservationStatus] = mapped_column(
    Enum(OfferReservationStatus, name="offer_reservation_status", create_type=False),
    nullable=False,
    server_default=OfferReservationStatus.PENDING.value,
  )
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

  offer = relationship("Offer")
