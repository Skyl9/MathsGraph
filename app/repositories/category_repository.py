from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Category
from .base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)

    async def get_by_name(self, name: str):
        query = select(Category).where(Category.nom == name)
        result = await self.db.execute(query)
        return result.scalars().first()
