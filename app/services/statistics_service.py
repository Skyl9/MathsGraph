import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db_utils import get_id_by_field
from app.core.exceptions import NotFoundException
from app.db.models import ConceptView

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_concept_views(self, concept_id: int):
        # Vérifier que le concept existe
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept not found")
        
        query = (
            select(
                func.count().label("view_count"),
                func.count(ConceptView.user_id.distinct()).label("unique_viewers")
            )
            .where(ConceptView.concept_id == concept_id)
        )
        result = await self.db.execute(query)
        row = result.one()
        
        if row.view_count > 0:
            return {"total_views": row.view_count, "unique_viewers": row.unique_viewers}
        else:
            return {"total_views": 0, "unique_viewers": 0}
