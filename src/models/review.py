from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.models.base import Base, TimestampCreatedMixin


class Review(Base, TimestampCreatedMixin):
  __tablename__ = "reviews"
  __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),)

  id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
  venue_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
  order_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
  rating: Mapped[int] = mapped_column(Integer, nullable=False)
  comment: Mapped[str | None] = mapped_column(Text, nullable=True)
  images_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
  deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
