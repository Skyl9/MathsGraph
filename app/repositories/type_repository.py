from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Type


class TypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_types(self):
        query = select(Type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, id_type: int):
        return await self.db.get(Type, id_type)

    async def get_by_name(self, nom: str):
        query = select(Type).where(Type.type == nom)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add(self, t: Type):
        self.db.add(t)
        await self.db.flush()

    async def flush(self):
        await self.db.flush()
