from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        query = select(Category)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, id_category: int):
        return await self.db.get(Category, id_category)

    async def get_by_name(self, name: str):
        query = select(Category).where(Category.nom == name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add(self, category: Category):
        self.db.add(category)
        await self.db.flush()
        return category

    async def flush(self):
        await self.db.flush()
