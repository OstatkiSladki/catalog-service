from __future__ import annotations

from src.models.category import Category
from src.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):

    model = Category

    async def get_tree(self) -> list[Category]:
        stmt = self._base_query().where(Category.parent_id.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_children(self, parent_id: int) -> list[Category]:
        stmt = self._base_query().where(Category.parent_id == parent_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = self._base_query().where(Category.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
