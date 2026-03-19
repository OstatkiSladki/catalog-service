from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime

from src.models.base import Base, TimestampCreatedMixin, TimestampUpdatedMixin

if TYPE_CHECKING:
  from src.models.offer_item import OfferItem
  from src.models.product_category import ProductCategory


class Product(Base, TimestampCreatedMixin, TimestampUpdatedMixin):
  __tablename__ = "products"

  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(255), nullable=False)
  description: Mapped[str | None] = mapped_column(Text, nullable=True)
  image_urls: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
  characteristics_json: Mapped[dict[str, Any]] = mapped_column(
    JSONB,
    nullable=False,
    server_default="{}",
  )
  is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
  deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

  category_links: Mapped[list[ProductCategory]] = relationship(back_populates="product")
  offer_items: Mapped[list[OfferItem]] = relationship(back_populates="product")
