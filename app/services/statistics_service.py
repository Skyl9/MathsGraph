from psycopg import AsyncConnection
from app.utils.db_utils import get_id_by_field


import logging

from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_concept_views(self,concept_id: int):
            await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept not found")
            async with self.db.cursor() as cursor:
                await cursor.execute("""
                               SELECT COUNT(*)                as view_count,
                                      COUNT(DISTINCT user_id) as unique_viewers
                               FROM concept_views
                               WHERE concept_id = %s
                               """, (concept_id,))
                result = await cursor.fetchone()
                if result[0]>0:
                    return {"total_views": result[0], "unique_viewers": result[1]}
                else:
                    return {"total_views": 0, "unique_viewers": 0}
