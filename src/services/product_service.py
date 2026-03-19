from __future__ import annotations

from src.models.product import Product
from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductUpdate


class ProductValidationError(ValueError):
  pass


class ProductService:
  def __init__(self, repository: ProductRepository) -> None:
    self.repository = repository

  async def get_by_id(self, product_id: int) -> Product | None:
    return await self.repository.get_by_id(product_id)

  async def list_products(
    self,
    *,
    category_id: int | None,
    search: str | None,
    offset: int,
    limit: int,
  ) -> tuple[list[Product], int]:
    items = await self.repository.list_filtered(
      category_id=category_id,
      search=search,
      offset=offset,
      limit=limit,
    )
    total_count = await self.repository.count_filtered(category_id=category_id, search=search)
    return items, total_count

  async def list_by_category(
    self,
    category_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Product]:
    return await self.repository.list_by_category(category_id, offset=offset, limit=limit)

  async def search(self, query: str, *, offset: int = 0, limit: int = 20) -> list[Product]:
    return await self.repository.search(query, offset=offset, limit=limit)

  async def create(self, payload: ProductCreate) -> Product:
    if not payload.category_ids:
      raise ProductValidationError("Product must have at least one category")
    data = payload.model_dump()
    category_ids = data.pop("category_ids")
    return await self.repository.create_with_categories(data, category_ids)

  async def update(self, product_id: int, payload: ProductUpdate) -> Product | None:
    category_ids = payload.category_ids
    if category_ids is not None and not category_ids:
      raise ProductValidationError("Product must have at least one category")
    data = payload.model_dump(exclude_unset=True)
    data.pop("category_ids", None)
    return await self.repository.update_with_categories(product_id, data, category_ids)

  async def archive(self, product_id: int) -> bool:
    return await self.repository.soft_delete(product_id)
