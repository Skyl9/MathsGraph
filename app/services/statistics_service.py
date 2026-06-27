import logging
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db_utils import get_id_by_field
from app.db.models import ConceptView
from app.repositories.statistics_repository import StatisticsRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StatisticsRepository(db)

    async def get_concept_views(self, concept_id: int):
        # Vérifier que le concept existe
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept not found")

        row = await self.repo.get_views_for_concept(concept_id)

        if row.view_count > 0:
            return {"total_views": row.view_count, "unique_viewers": row.unique_viewers}
        else:
            return {"total_views": 0, "unique_viewers": 0}

    async def add_concept_view(self, concept_id: int, user_id: PyUUID | None = None, ip_address: str | None = None):
        # Vérifier que le concept existe
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept not found")

        view = ConceptView(concept_id=concept_id, user_id=user_id, ip_address=ip_address)
        await self.repo.add_view(view)
        return {"message": "Vue enregistrée"}
