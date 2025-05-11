from app.db.database import get_db_connection


class StatisticsService:
    @staticmethod
    def get_concept_views(concept_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                           SELECT COUNT(*)                as view_count,
                                  COUNT(DISTINCT user_id) as unique_viewers
                           FROM concept_views
                           WHERE concept_id = %s
                           """, (concept_id,))
            result = cursor.fetchone()
            return {"total_views": result[0], "unique_viewers": result[1]}
        finally:
            cursor.close()
            conn.close()