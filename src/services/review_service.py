from __future__ import annotations

from src.api.deps import IdentityContext
from src.models.review import Review
from src.repositories.review_repository import ReviewRepository
from src.schemas.review import ReviewCreate, ReviewUpdate


class ReviewForbiddenError(PermissionError):
  pass


class ReviewService:
  def __init__(self, repository: ReviewRepository) -> None:
    self.repository = repository

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

  async def create(self, payload: ReviewCreate, identity: IdentityContext) -> Review:
    if identity.user_role == "staff":
      raise ReviewForbiddenError("Staff cannot create reviews")
    existing = await self.repository.get_by_order(payload.order_id)
    if existing is not None:
      raise ValueError("Review for this order already exists")
    data = payload.model_dump()
    data["user_id"] = int(identity.user_id)
    # TODO: spec://com.ostatki.catalog/PROP-001#business.rules
    # Validate order ownership via Order Service gRPC.
    return await self.repository.create(data)

  async def update(
    self,
    review_id: int,
    payload: ReviewUpdate,
    identity: IdentityContext,
  ) -> Review | None:
    review = await self.repository.get_by_id(review_id)
    if review is None:
      return None
    self._ensure_can_manage_review(identity, review.user_id)
    return await self.repository.update(review_id, payload.model_dump(exclude_unset=True))

  async def archive(self, review_id: int, identity: IdentityContext) -> bool:
    review = await self.repository.get_by_id(review_id)
    if review is None:
      return False
    self._ensure_can_manage_review(identity, review.user_id)
    return await self.repository.soft_delete(review_id)

  def _ensure_can_manage_review(self, identity: IdentityContext, owner_user_id: int) -> None:
    if identity.user_role == "admin":
      return
    if identity.user_role == "staff":
      raise ReviewForbiddenError("Staff cannot manage reviews")
    if int(identity.user_id) != owner_user_id:
      raise ReviewForbiddenError("Only review author can manage this review")
