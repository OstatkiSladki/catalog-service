from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total_count: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, object] | None = None
    timestamp: datetime
    request_id: str
    trace_id: str | None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    version: str
