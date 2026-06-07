from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from app.db.models import Concept, Relation, Position
from app.schemas.enums import VueLayout


class LayoutRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_concepts_with_mathematicien(self):
        query = select(Concept).options(joinedload(Concept.mathematicien)).order_by(Concept.id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_edges(self):
        query = select(Relation.concept_source, Relation.concept_cible)
        result = await self.db.execute(query)
        return result.all()

    async def delete_positions_by_views(self, views: list[VueLayout]):
        await self.db.execute(delete(Position).where(Position.vue.in_(views)))

    def add_all_positions(self, positions: list[Position]):
        self.db.add_all(positions)

    async def flush(self):
        await self.db.flush()
