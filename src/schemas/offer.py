from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.models.offer import OfferStatus


class OfferListQuery(BaseModel):
  page: int = Field(default=1, ge=1)
  limit: int = Field(default=20, ge=1, le=100)
  venue_id: int | None = Field(default=None, ge=1)
  status: OfferStatus | None = None
  category_id: int | None = Field(default=None, ge=1)


class OfferItemBase(BaseModel):
  product_id: int = Field(ge=1)
  quantity: int = Field(default=1, ge=1)


class OfferItemCreate(OfferItemBase):
  pass


class OfferItem(OfferItemBase):
  model_config = ConfigDict(from_attributes=True)

  id: int


class OfferCreate(BaseModel):
  venue_id: int = Field(ge=1)
  current_price: Decimal = Field(gt=0)
  original_price: Decimal = Field(gt=0)
  quantity_available: int = Field(default=1, ge=1)
  expires_at: datetime
  items: Annotated[list[OfferItemCreate], Field(min_length=1)]


class OfferUpdate(BaseModel):
  current_price: Decimal | None = Field(default=None, gt=0)
  original_price: Decimal | None = Field(default=None, gt=0)
  quantity_available: int | None = Field(default=None, ge=1)
  expires_at: datetime | None = None
  status: OfferStatus | None = None
  items: list[OfferItemCreate] | None = None


class Offer(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  venue_id: int
  current_price: Decimal
  original_price: Decimal
  quantity_available: int
  expires_at: datetime
  status: OfferStatus
  items: list[OfferItem] = Field(default_factory=list)
  created_at: datetime
  updated_at: datetime
