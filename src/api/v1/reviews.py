from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import IntegrityError

from src.api import exceptions
from src.api.deps import (
  InternalAuthHeaders,
  get_internal_auth_headers,
  get_optional_auth_headers,
  get_review_repository,
)
from src.repositories.review_repository import ReviewRepository
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.review import Review as ReviewSchema
from src.schemas.review import ReviewCreate, ReviewListQuery, ReviewUpdate
from src.services.review_service import ReviewForbiddenError, ReviewService

router = APIRouter(prefix="/reviews")


def _get_service(repository: ReviewRepository) -> ReviewService:
  return ReviewService(repository)


def _offset(page: int, limit: int) -> int:
  return (page - 1) * limit


@router.get("", response_model=PaginatedResponse[ReviewSchema])
async def list_reviews(
  repository: Annotated[ReviewRepository, Depends(get_review_repository)],
  params: Annotated[ReviewListQuery, Query()],
  identity: Annotated[InternalAuthHeaders | None, Depends(get_optional_auth_headers)],
) -> PaginatedResponse[ReviewSchema]:
  if params.user_id is not None:
    if identity is None:
      raise exceptions.identity_required()
    if identity.user_role != "admin" and int(identity.user_id) != params.user_id:
      raise exceptions.own_reviews_filter_only()

  service = _get_service(repository)
  items, total_count = await service.list(
    venue_id=params.venue_id,
    user_id=params.user_id,
    offset=_offset(params.page, params.limit),
    limit=params.limit,
  )
  return PaginatedResponse(
    items=[ReviewSchema.model_validate(item) for item in items],
    pagination=PaginationMeta(page=params.page, limit=params.limit, total_count=total_count),
  )


@router.get("/{review_id}", response_model=ReviewSchema)
async def get_review(
  review_id: int,
  repository: Annotated[ReviewRepository, Depends(get_review_repository)],
) -> ReviewSchema:
  service = _get_service(repository)
  review = await service.get_by_id(review_id)
  if review is None:
    raise exceptions.review_not_found()
  return ReviewSchema.model_validate(review)


@router.post("", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
  repository: Annotated[ReviewRepository, Depends(get_review_repository)],
  identity: Annotated[InternalAuthHeaders, Depends(get_internal_auth_headers)],
  payload: ReviewCreate,
) -> ReviewSchema:
  service = _get_service(repository)
  try:
    review = await service.create(payload, identity)
    return ReviewSchema.model_validate(review)
  except ReviewForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc
  except ValueError as exc:
    raise exceptions.conflict(str(exc)) from exc
  except IntegrityError as exc:
    raise exceptions.review_conflict() from exc


@router.patch("/{review_id}", response_model=ReviewSchema)
async def update_review(
  repository: Annotated[ReviewRepository, Depends(get_review_repository)],
  identity: Annotated[InternalAuthHeaders, Depends(get_internal_auth_headers)],
  review_id: int,
  payload: ReviewUpdate,
) -> ReviewSchema:
  service = _get_service(repository)
  try:
    review = await service.update(review_id, payload, identity)
    if review is None:
      raise exceptions.review_not_found()
    return ReviewSchema.model_validate(review)
  except ReviewForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc


@router.delete(
  "/{review_id}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_class=Response,
)
async def delete_review(
  repository: Annotated[ReviewRepository, Depends(get_review_repository)],
  identity: Annotated[InternalAuthHeaders, Depends(get_internal_auth_headers)],
  review_id: int,
) -> Response:
  service = _get_service(repository)
  try:
    deleted = await service.archive(review_id, identity)
    if not deleted:
      raise exceptions.review_not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
  except ReviewForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc
