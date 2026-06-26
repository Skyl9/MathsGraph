from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Mathematicien
from .base_repository import BaseRepository


class MathematicienRepository(BaseRepository[Mathematicien]):
    def __init__(self, db: AsyncSession):
        super().__init__(Mathematicien, db)

    async def get_all_names(self):
        query = select(Mathematicien.id, Mathematicien.nom)
        result = await self.db.execute(query)
        return result.all()

    async def get_id_by_name(self, nom: str):
        query = select(Mathematicien.id).where(Mathematicien.nom == nom)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_timeline_data(self):
        query = (
            select(Mathematicien)
            .where(Mathematicien.date_naissance.isnot(None))
            .order_by(Mathematicien.date_naissance.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()
