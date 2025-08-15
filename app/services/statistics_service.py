from psycopg import AsyncConnection


import logging

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_concept_views(self,concept_id: int):
        try:
            async with self.db.cursor() as cursor:
                await cursor.execute("""
                               SELECT COUNT(*)                as view_count,
                                      COUNT(DISTINCT user_id) as unique_viewers
                               FROM concept_views
                               WHERE concept_id = %s
                               """, (concept_id,))
                result = await cursor.fetchone()
                return {"total_views": result[0], "unique_viewers": result[1]}
        except:
            return {"total_views": 0, "unique_viewers": 0}
