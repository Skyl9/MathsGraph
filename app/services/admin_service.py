from app.db.database import get_db_connection


class AdminService:
    @staticmethod
    def get_stats():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""SELECT (SELECT COUNT(*) FROM users)          AS users,
                                     (SELECT COUNT(*) FROM user_favorites) AS favorites,
                                     (SELECT COUNT(*) FROM concepts)       AS concepts,
                                     (SELECT COUNT(*) FROM categories)     AS categories,
                                    (SELECT COUNT(*) FROM mathematiciens) AS mathematicien;
                           """)
            data = cursor.fetchone()
            print(data)
            return {"users": data[0], "favorites": data[1], "concepts": data[2], "categories": data[3],"mathematicien":data[4],}

    @staticmethod
    def get_users():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""SELECT id,username, email,role, is_active, created_at FROM users;""")
            data = cursor.fetchall()
            returnValue = []
            for i in data:
                returnValue.append({"id":i[0],"username":i[1],"email":i[2],"role":i[3],"is_active":i[4],"created_at":i[5]})
            return returnValue
    @staticmethod
    def get_contents():
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""SELECT concepts.id,concepts.nom,type.type FROM concepts LEFT JOIN type ON type.id = concepts.type_id;""")
            data = cursor.fetchall()
            returnValue = []
            for i in data:
                returnValue.append({"id":i[0],"nom":i[1],"type":i[2]})
            return returnValue