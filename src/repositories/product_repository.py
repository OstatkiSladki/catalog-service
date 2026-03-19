from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, func, select

from src.models.product import Product
from src.models.product_category import ProductCategory
from src.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
  model = Product

  async def create_with_categories(
    self,
    data: dict[str, object],
    category_ids: Sequence[int],
  ) -> Product:
    product = Product(**data)
    product.category_links = [
      ProductCategory(category_id=category_id) for category_id in category_ids
    ]
    self.session.add(product)
    return product

  async def update_with_categories(
    self,
    product_id: int,
    data: dict[str, object],
    category_ids: Sequence[int] | None,
  ) -> Product | None:
    product = await self.update(product_id, data)
    if product is None:
      return None
    if category_ids is not None:
      await self._replace_categories(product_id, category_ids)
      refreshed = await self.get_by_id(product_id)
      if refreshed is None:
        return None
      return refreshed
    return product

  async def list_filtered(
    self,
    *,
    category_id: int | None,
    search: str | None,
    offset: int,
    limit: int,
  ) -> list[Product]:
    stmt = select(Product).where(Product.deleted_at.is_(None))
    if category_id is not None:
      stmt = stmt.join(ProductCategory, ProductCategory.product_id == Product.id).where(
        ProductCategory.category_id == category_id,
      )
    if search:
      stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    stmt = stmt.offset(offset).limit(limit)
    result = await self.session.execute(stmt)
    return list(result.scalars().all())

  async def count_filtered(self, *, category_id: int | None, search: str | None) -> int:
    stmt = select(func.count(func.distinct(Product.id))).where(Product.deleted_at.is_(None))
    if category_id is not None:
      stmt = stmt.join(ProductCategory, ProductCategory.product_id == Product.id).where(
        ProductCategory.category_id == category_id,
      )
    if search:
      stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    result = await self.session.execute(stmt)
    return int(result.scalar_one())

  async def list_by_category(
    self,
    category_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
  ) -> list[Product]:
    return await self.list_filtered(
      category_id=category_id,
      search=None,
      offset=offset,
      limit=limit,
    )

  async def search(self, query: str, *, offset: int = 0, limit: int = 20) -> list[Product]:
    return await self.list_filtered(
      category_id=None,
      search=query,
      offset=offset,
      limit=limit,
    )

  async def _replace_categories(self, product_id: int, category_ids: Sequence[int]) -> None:
    await self.session.execute(
      delete(ProductCategory).where(ProductCategory.product_id == product_id),
    )
    for category_id in category_ids:
      self.session.add(ProductCategory(product_id=product_id, category_id=category_id))
