from psycopg import AsyncConnection


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
                SELECT id, username, email, role, is_active, created_at FROM users;
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

    async def get_contents(self):
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