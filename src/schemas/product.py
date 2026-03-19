from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ProductListQuery(BaseModel):
  page: int = Field(default=1, ge=1)
  limit: int = Field(default=20, ge=1, le=100)
  category_id: int | None = Field(default=None, ge=1)
  search: str | None = Field(default=None, min_length=1, max_length=200)


CategoryIds = Annotated[list[int], Field(min_length=1)]


class ProductBase(BaseModel):
  name: str = Field(min_length=1, max_length=255)
  description: str | None = None
  image_urls: list[str] = Field(default_factory=list)
  characteristics_json: dict[str, object] = Field(default_factory=dict)
  is_active: bool = True


class ProductCreate(ProductBase):
  category_ids: CategoryIds


class ProductUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=255)
  description: str | None = None
  image_urls: list[str] | None = None
  characteristics_json: dict[str, object] | None = None
  is_active: bool | None = None
  category_ids: list[int] | None = None


class Product(ProductBase):
  model_config = ConfigDict(from_attributes=True)

  id: int
  created_at: datetime
  updated_at: datetime
  deleted_at: datetime | None = None
