from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import IntegrityError

from src.api import exceptions
from src.api.deps import (
  IdentityContext,
  get_offer_repository,
  require_staff_or_admin,
)
from src.repositories.offer_repository import OfferRepository
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.offer import Offer as OfferSchema
from src.schemas.offer import OfferCreate, OfferListQuery, OfferUpdate
from src.services.offer_service import OfferForbiddenError, OfferService, OfferValidationError

router = APIRouter(prefix="/offers")


def _get_service(repository: OfferRepository) -> OfferService:
  return OfferService(repository)


def _offset(page: int, limit: int) -> int:
  return (page - 1) * limit


@router.get("", response_model=PaginatedResponse[OfferSchema])
async def list_offers(
  repository: Annotated[OfferRepository, Depends(get_offer_repository)],
  params: Annotated[OfferListQuery, Query()],
) -> PaginatedResponse[OfferSchema]:
  service = _get_service(repository)
  items, total_count = await service.list(
    venue_id=params.venue_id,
    status=params.status,
    category_id=params.category_id,
    offset=_offset(params.page, params.limit),
    limit=params.limit,
  )
  return PaginatedResponse(
    items=[OfferSchema.model_validate(item) for item in items],
    pagination=PaginationMeta(page=params.page, limit=params.limit, total_count=total_count),
  )


@router.get("/{offer_id}", response_model=OfferSchema)
async def get_offer(
  offer_id: int,
  repository: Annotated[OfferRepository, Depends(get_offer_repository)],
) -> OfferSchema:
  service = _get_service(repository)
  offer = await service.get_by_id(offer_id)
  if offer is None:
    raise exceptions.offer_not_found()
  return OfferSchema.model_validate(offer)


@router.post("", response_model=OfferSchema)
async def create_offer(
  repository: Annotated[OfferRepository, Depends(get_offer_repository)],
  identity: Annotated[IdentityContext, Depends(require_staff_or_admin)],
  payload: OfferCreate,
) -> OfferSchema:
  service = _get_service(repository)
  try:
    offer = await service.create(payload, identity)
    return OfferSchema.model_validate(offer)
  except OfferForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc
  except OfferValidationError as exc:
    raise exceptions.bad_request(str(exc)) from exc
  except IntegrityError as exc:
    raise exceptions.venue_or_product_not_found() from exc


@router.patch("/{offer_id}", response_model=OfferSchema)
async def update_offer(
  repository: Annotated[OfferRepository, Depends(get_offer_repository)],
  identity: Annotated[IdentityContext, Depends(require_staff_or_admin)],
  offer_id: int,
  payload: OfferUpdate,
) -> OfferSchema:
  service = _get_service(repository)
  try:
    offer = await service.update(offer_id, payload, identity)
    if offer is None:
      raise exceptions.offer_not_found()
    return OfferSchema.model_validate(offer)
  except OfferForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc
  except OfferValidationError as exc:
    raise exceptions.bad_request(str(exc)) from exc
  except IntegrityError as exc:
    raise exceptions.invalid_offer_items() from exc


@router.delete(
  "/{offer_id}",
  status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_offer(
  repository: Annotated[OfferRepository, Depends(get_offer_repository)],
  identity: Annotated[IdentityContext, Depends(require_staff_or_admin)],
  offer_id: int,
) -> Response:
  service = _get_service(repository)
  try:
    cancelled = await service.cancel(offer_id, identity)
    if not cancelled:
      raise exceptions.offer_not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
  except OfferForbiddenError as exc:
    raise exceptions.forbidden(str(exc)) from exc
