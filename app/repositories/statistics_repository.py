from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import ConceptView


class StatisticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_views_for_concept(self, concept_id: int):
        query = select(
            func.count().label("view_count"), func.count(ConceptView.user_id.distinct()).label("unique_viewers")
        ).where(ConceptView.concept_id == concept_id)
        result = await self.db.execute(query)
        return result.one()

    async def add_view(self, view: ConceptView):
        self.db.add(view)
        await self.db.commit()
