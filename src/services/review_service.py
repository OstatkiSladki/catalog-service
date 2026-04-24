from __future__ import annotations

import grpc

from src.api.deps import InternalAuthHeaders
from src.grpc.clients import CircuitBreakerOpenError, GrpcDependencyError, OrderQueryClient
from src.models.review import Review
from src.repositories.review_repository import ReviewRepository
from src.schemas.review import ReviewCreate, ReviewUpdate


class ReviewForbiddenError(PermissionError):
  pass


class ReviewDependencyError(RuntimeError):
  pass


class ReviewService:
  def __init__(self, repository: ReviewRepository, order_client: OrderQueryClient) -> None:
    self.repository = repository
    self.order_client = order_client

  async def get_by_id(self, review_id: int) -> Review | None:
    return await self.repository.get_by_id(review_id)

  async def list(
    self,
    *,
    venue_id: int | None,
    user_id: int | None,
    offset: int,
    limit: int,
  ) -> tuple[list[Review], int]:
    items = await self.repository.list_filtered(
      venue_id=venue_id,
      user_id=user_id,
      offset=offset,
      limit=limit,
    )
    total_count = await self.repository.count_filtered(venue_id=venue_id, user_id=user_id)
    return items, total_count

  async def create(self, payload: ReviewCreate, identity: InternalAuthHeaders) -> Review:
    if identity.user_role == "staff":
      raise ReviewForbiddenError("Staff cannot create reviews")
    existing = await self.repository.get_by_order(payload.order_id)
    if existing is not None:
      raise ValueError("Review for this order already exists")
    await self._validate_order(payload, identity)
    data = payload.model_dump()
    data["user_id"] = int(identity.user_id)
    return await self.repository.create(data)

  async def update(
    self,
    review_id: int,
    payload: ReviewUpdate,
    identity: InternalAuthHeaders,
  ) -> Review | None:
    review = await self.repository.get_by_id(review_id)
    if review is None:
      return None
    self._ensure_can_manage_review(identity, review.user_id)
    return await self.repository.update(review_id, payload.model_dump(exclude_unset=True))

  async def archive(self, review_id: int, identity: InternalAuthHeaders) -> bool:
    review = await self.repository.get_by_id(review_id)
    if review is None:
      return False
    self._ensure_can_manage_review(identity, review.user_id)
    return await self.repository.soft_delete(review_id)

  def _ensure_can_manage_review(self, identity: InternalAuthHeaders, owner_user_id: int) -> None:
    if identity.user_role == "admin":
      return
    if identity.user_role == "staff":
      raise ReviewForbiddenError("Staff cannot manage reviews")
    if int(identity.user_id) != owner_user_id:
      raise ReviewForbiddenError("Only review author can manage this review")

  async def _validate_order(self, payload: ReviewCreate, identity: InternalAuthHeaders) -> None:
    try:
      order = await self.order_client.get_order_by_id(payload.order_id)
    except grpc.aio.AioRpcError as exc:
      if exc.code() == grpc.StatusCode.NOT_FOUND:
        raise ValueError("Order not found") from exc
      raise ReviewDependencyError("Order gRPC validation failed") from exc
    except (GrpcDependencyError, CircuitBreakerOpenError) as exc:
      raise ReviewDependencyError("Order gRPC validation failed") from exc

    if int(order.user_id) != int(identity.user_id):
      raise ValueError("Order does not belong to the user")
    if int(order.venue_id) != int(payload.venue_id):
      raise ValueError("Order venue does not match review venue")
