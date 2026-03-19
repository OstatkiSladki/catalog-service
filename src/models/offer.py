from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime

from src.models.base import Base, TimestampCreatedMixin, TimestampUpdatedMixin

if TYPE_CHECKING:
    from src.models.offer_item import OfferItem


class OfferStatus(StrEnum):
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Offer(Base, TimestampCreatedMixin, TimestampUpdatedMixin):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, name="offer_status", create_type=False),
        nullable=False,
        server_default=OfferStatus.ACTIVE.value,
    )

    items: Mapped[list[OfferItem]] = relationship(back_populates="offer")
