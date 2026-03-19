from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime

from src.models.base import Base, TimestampCreatedMixin

if TYPE_CHECKING:
  from src.models.product_category import ProductCategory


class Category(Base, TimestampCreatedMixin):
  __tablename__ = "categories"

  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
  parent_id: Mapped[int | None] = mapped_column(
    BigInteger,
    ForeignKey("categories.id", ondelete="SET NULL"),
    nullable=True,
  )
  is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
  deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

  parent: Mapped[Category | None] = relationship(
    "Category",
    remote_side=[id],
    back_populates="children",
  )
  children: Mapped[list[Category]] = relationship("Category", back_populates="parent")
  product_links: Mapped[list[ProductCategory]] = relationship(back_populates="category")
