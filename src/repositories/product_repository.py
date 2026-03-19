from __future__ import annotations

from sqlalchemy import select

from src.models.product import Product
from src.models.product_category import ProductCategory
from src.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):

    model = Product

    async def list_by_category(
        self,
        category_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Product]:
        stmt = (
            select(Product)
            .join(ProductCategory, ProductCategory.product_id == Product.id)
            .where(ProductCategory.category_id == category_id)
            .where(Product.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, query: str, *, offset: int = 0, limit: int = 20) -> list[Product]:
        stmt = (
            self._base_query()
            .where(Product.name.ilike(f"%{query}%"))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
