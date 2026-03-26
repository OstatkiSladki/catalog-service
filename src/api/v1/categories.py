from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import IntegrityError

from src.api import exceptions
from src.api.deps import InternalAuthHeaders, get_category_repository, require_admin
from src.repositories.category_repository import CategoryRepository
from src.schemas.category import Category as CategorySchema
from src.schemas.category import CategoryCreate, CategoryListQuery, CategoryUpdate
from src.services.category_service import CategoryService, SlugAlreadyExistsError

router = APIRouter(prefix="/categories")


def _get_service(repository: CategoryRepository) -> CategoryService:
  return CategoryService(repository)


@router.get("", response_model=list[CategorySchema])
async def list_categories(
  repository: Annotated[CategoryRepository, Depends(get_category_repository)],
  params: Annotated[CategoryListQuery, Query()],
) -> list[CategorySchema]:
  service = _get_service(repository)
  items = await service.list(parent_id=params.parent_id, limit=params.limit)
  return [CategorySchema.model_validate(item) for item in items]


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(
  category_id: int,
  repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategorySchema:
  service = _get_service(repository)
  category = await service.get_by_id(category_id)
  if category is None:
    raise exceptions.category_not_found()
  return CategorySchema.model_validate(category)


@router.post("", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
  repository: Annotated[CategoryRepository, Depends(get_category_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  payload: CategoryCreate,
) -> CategorySchema:
  service = _get_service(repository)
  try:
    category = await service.create(payload)
    return CategorySchema.model_validate(category)
  except SlugAlreadyExistsError as exc:
    raise exceptions.slug_already_exists() from exc
  except IntegrityError as exc:
    raise exceptions.slug_already_exists() from exc


@router.patch("/{category_id}", response_model=CategorySchema)
async def update_category(
  repository: Annotated[CategoryRepository, Depends(get_category_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  category_id: int,
  payload: CategoryUpdate,
) -> CategorySchema:
  service = _get_service(repository)
  try:
    category = await service.update(category_id, payload)
    if category is None:
      raise exceptions.category_not_found()
    return CategorySchema.model_validate(category)
  except SlugAlreadyExistsError as exc:
    raise exceptions.slug_already_exists() from exc
  except IntegrityError as exc:
    raise exceptions.slug_already_exists() from exc


@router.delete(
  "/{category_id}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_class=Response,
)
async def delete_category(
  repository: Annotated[CategoryRepository, Depends(get_category_repository)],
  _: Annotated[InternalAuthHeaders, Depends(require_admin)],
  category_id: int,
) -> Response:
  service = _get_service(repository)
  deleted = await service.archive(category_id)
  if not deleted:
    raise exceptions.category_not_found()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
