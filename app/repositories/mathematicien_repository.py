from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Mathematicien


class MathematicienRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_names(self):
        query = select(Mathematicien.id, Mathematicien.nom)
        result = await self.db.execute(query)
        return result.all()

    async def get_by_id(self, id_mathematicien: int):
        return await self.db.get(Mathematicien, id_mathematicien)

    async def get_all_info(self):
        query = select(Mathematicien)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_id_by_name(self, nom: str):
        query = select(Mathematicien.id).where(Mathematicien.nom == nom)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add(self, math: Mathematicien):
        self.db.add(math)
        await self.db.flush()

    async def get_timeline_data(self):
        query = (
            select(Mathematicien)
            .where(Mathematicien.date_naissance.isnot(None))
            .order_by(Mathematicien.date_naissance.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def flush(self):
        await self.db.flush()
