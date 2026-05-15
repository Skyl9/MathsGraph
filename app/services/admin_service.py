import logging

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def get_stats(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                                 SELECT (SELECT COUNT(*) FROM users)          AS users,
                                        (SELECT COUNT(*) FROM user_favorites) AS favorites,
                                        (SELECT COUNT(*) FROM concepts)       AS concepts,
                                        (SELECT COUNT(*) FROM categories)     AS categories,
                                        (SELECT COUNT(*) FROM mathematiciens) AS mathematicien;
                                 """)
            data = await cursor.fetchone()
            return {
                "users": data[0],
                "favorites": data[1],
                "concepts": data[2],
                "categories": data[3],
                "mathematicien": data[4],
            }

    async def get_users(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                                 SELECT id, username, email, role, is_active, created_at
                                 FROM users;
                                 """)
            data = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "role": row[3],
                    "is_active": row[4],
                    "created_at": row[5],
                }
                for row in data
            ]

    async def get_concepts_admin(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                                 SELECT concepts.id, concepts.nom, type.type
                                 FROM concepts
                                          LEFT JOIN type ON type.id = concepts.type_id;
                                 """)
            data = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "nom": row[1],
                    "type": row[2],
                }
                for row in data
            ]

    async def get_api_analytics(self):
        async with self.db.cursor() as cursor:
            # Top 10 des routes les plus appelées, avec leur temps de réponse moyen
            await cursor.execute("""
                                 SELECT method,
                                        endpoint,
                                        COUNT(*)                            as total_hits,
                                        ROUND(AVG(duration_ms)::numeric, 2) as avg_duration_ms
                                 FROM api_logs
                                 GROUP BY method, endpoint
                                 ORDER BY total_hits DESC
                                 LIMIT 10;
                                 """)
            top_routes = await cursor.fetchall()

            # Nombre total de requêtes aujourd'hui
            await cursor.execute("""
                                 SELECT COUNT(*)
                                 FROM api_logs
                                 WHERE created_at >= CURRENT_DATE;
                                 """)
            daily_hits = await cursor.fetchone()

            return {
                "daily_hits": daily_hits[0],
                "top_routes": [
                    {
                        "method": row[0],
                        "endpoint": row[1],
                        "total_hits": row[2],
                        "avg_duration": float(row[3])
                    } for row in top_routes
                ]
            }
