from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Type
from .base_repository import BaseRepository


class TypeRepository(BaseRepository[Type]):
    def __init__(self, db: AsyncSession):
        super().__init__(Type, db)

    async def get_by_name(self, nom: str):
        query = select(Type).where(Type.type == nom)
        result = await self.db.execute(query)
        return result.scalars().first()
