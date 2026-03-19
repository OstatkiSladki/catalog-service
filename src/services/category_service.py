from __future__ import annotations

from src.models.category import Category
from src.repositories.category_repository import CategoryRepository
from src.schemas.category import CategoryCreate, CategoryUpdate


class SlugAlreadyExistsError(ValueError):
  pass


class CategoryService:
  def __init__(self, repository: CategoryRepository) -> None:
    self.repository = repository

  async def get_by_id(self, category_id: int) -> Category | None:
    return await self.repository.get_by_id(category_id)

  async def list(
    self,
    *,
    parent_id: int | None,
    limit: int = 20,
  ) -> list[Category]:
    return await self.repository.list(
      filters={"parent_id": parent_id, "is_active": True},
      limit=limit,
    )

  async def create(self, payload: CategoryCreate) -> Category:
    existing = await self.repository.get_by_slug(payload.slug)
    if existing is not None:
      raise SlugAlreadyExistsError(payload.slug)
    return await self.repository.create(payload.model_dump())

  async def update(self, category_id: int, payload: CategoryUpdate) -> Category | None:
    if payload.slug is not None:
      existing = await self.repository.get_by_slug(payload.slug)
      if existing is not None and existing.id != category_id:
        raise SlugAlreadyExistsError(payload.slug)
    return await self.repository.update(category_id, payload.model_dump(exclude_unset=True))

  async def archive(self, category_id: int) -> bool:
    return await self.repository.soft_delete(category_id)
