from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import IntegrityError

from src.api import exceptions
from src.api.deps import InternalAuthHeaders, get_product_repository, require_admin
from src.repositories.product_repository import ProductRepository
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.product import Product as ProductSchema
from src.schemas.product import ProductCreate, ProductListQuery, ProductUpdate
from src.services.product_service import ProductService, ProductValidationError

router = APIRouter(prefix="/products")


def _get_service(repository: ProductRepository) -> ProductService:
  return ProductService(repository)


def _offset(page: int, limit: int) -> int:
  return (page - 1) * limit


@router.get("", response_model=PaginatedResponse[ProductSchema])
async def list_products(
  repository: Annotated[ProductRepository, Depends(get_product_repository)],
  params: Annotated[ProductListQuery, Query()],
) -> PaginatedResponse[ProductSchema]:
  service = _get_service(repository)
  items, total_count = await service.list_products(
    category_id=params.category_id,
    search=params.search,
    offset=_offset(params.page, params.limit),
    limit=params.limit,
  )
  return PaginatedResponse(
    items=[ProductSchema.model_validate(item) for item in items],
    pagination=PaginationMeta(page=params.page, limit=params.limit, total_count=total_count),
  )


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
  product_id: int,
  repository: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductSchema:
  service = _get_service(repository)
  product = await service.get_by_id(product_id)
  if product is None:
    raise exceptions.product_not_found()
  return ProductSchema.model_validate(product)


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
  repository: Annotated[ProductRepository, Depends(get_product_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  payload: ProductCreate,
) -> ProductSchema:
  service = _get_service(repository)
  try:
    product = await service.create(payload)
    return ProductSchema.model_validate(product)
  except ProductValidationError as exc:
    raise exceptions.bad_request(str(exc)) from exc
  except IntegrityError as exc:
    raise exceptions.invalid_category_relation() from exc


@router.patch("/{product_id}", response_model=ProductSchema)
async def update_product(
  repository: Annotated[ProductRepository, Depends(get_product_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  product_id: int,
  payload: ProductUpdate,
) -> ProductSchema:
  service = _get_service(repository)
  try:
    product = await service.update(product_id, payload)
    if product is None:
      raise exceptions.product_not_found()
    return ProductSchema.model_validate(product)
  except ProductValidationError as exc:
    raise exceptions.bad_request(str(exc)) from exc
  except IntegrityError as exc:
    raise exceptions.invalid_category_relation() from exc


@router.delete(
  "/{product_id}",
  status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
  repository: Annotated[ProductRepository, Depends(get_product_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  product_id: int,
) -> Response:
  service = _get_service(repository)
  deleted = await service.archive(product_id)
  if not deleted:
    raise exceptions.product_not_found()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
