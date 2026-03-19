from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewListQuery(BaseModel):
  page: int = Field(default=1, ge=1)
  limit: int = Field(default=20, ge=1, le=100)
  venue_id: int | None = Field(default=None, ge=1)
  user_id: int | None = Field(default=None, ge=1)


class ReviewCreate(BaseModel):
  order_id: int = Field(ge=1)
  venue_id: int = Field(ge=1)
  rating: int = Field(ge=1, le=5)
  comment: str | None = Field(default=None, max_length=1000)
  images_json: list[str] = Field(default_factory=list)


class ReviewUpdate(BaseModel):
  rating: int | None = Field(default=None, ge=1, le=5)
  comment: str | None = None
  images_json: list[str] | None = None


class Review(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: int
  venue_id: int
  order_id: int
  rating: int
  comment: str | None
  images_json: list[str] = Field(default_factory=list)
  created_at: datetime
