from psycopg import AsyncConnection


import logging

from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_concept_views(self,concept_id: int):
            async with self.db.cursor() as cursor:
                await cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
                if await cursor.fetchone() is None:
                    raise NotFoundException(detail="Concept not found")
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
