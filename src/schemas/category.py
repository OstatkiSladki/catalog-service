from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryListQuery(BaseModel):
  parent_id: int | None = Field(default=None, ge=1)
  limit: int = Field(default=20, ge=1, le=100)


class CategoryBase(BaseModel):
  name: str = Field(min_length=1, max_length=100)
  slug: str = Field(min_length=1, max_length=100)
  parent_id: int | None = None


class CategoryCreate(CategoryBase):
  pass


class CategoryUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=100)
  slug: str | None = Field(default=None, min_length=1, max_length=100)
  is_active: bool | None = None
  parent_id: int | None = None


class Category(CategoryBase):
  model_config = ConfigDict(from_attributes=True)

  id: int
  is_active: bool
  created_at: datetime
