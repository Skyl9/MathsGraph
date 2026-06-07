from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Alias


class AliasRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_alias(self, alias: str):
        query = select(Alias).where(Alias.alias == alias)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add(self, alias: Alias):
        self.db.add(alias)
        await self.db.flush()
        return alias
