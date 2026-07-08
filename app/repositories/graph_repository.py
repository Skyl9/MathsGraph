from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from app.db.models import Concept


class GraphRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_concepts_for_graph(self):
        stmt = (
            select(Concept)
            .options(
                joinedload(Concept.type),
                joinedload(Concept.category),
                joinedload(Concept.mathematicien),
                selectinload(Concept.positions),
                selectinload(Concept.outgoing_relations),
            )
            .order_by(Concept.id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
