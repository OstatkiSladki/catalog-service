from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampCreatedMixin

if TYPE_CHECKING:
  from src.models.offer import Offer
  from src.models.product import Product


class OfferItem(Base, TimestampCreatedMixin):
  __tablename__ = "offer_items"
  __table_args__ = (
    UniqueConstraint("offer_id", "product_id", name="uq_offer_items_offer_id_product_id"),
  )

  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  offer_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey("offers.id", ondelete="CASCADE"),
    nullable=False,
  )
  product_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey("products.id", ondelete="CASCADE"),
    nullable=False,
  )
  quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

  offer: Mapped[Offer] = relationship(back_populates="items")
  product: Mapped[Product] = relationship(back_populates="offer_items")
