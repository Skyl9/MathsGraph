from datetime import datetime

from fastapi import HTTPException, Depends
from psycopg import AsyncConnection

from app.core.exceptions import NotFoundException, InternalServerError
from app.db.database import get_db_connection, get_db
from app.schemas.user import UserId, UpdateUser, Favorite


class UserService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_user_by_id(self,id_user: int):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT id,username,email,is_active,created_at,role,preferred_language,avatar_url,bio FROM users WHERE id = %s;", (id_user,))
            user = await cursor.fetchone()
        if user is None:
            raise NotFoundException(detail="User not found")
        # Sérialisation du champ created_at
        created_at = user[4]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()  # Convertit datetime au format ISO 8601

        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_active": user[3],
            "created_at":created_at,
            "role": user[5],
            "preferred_language": user[6],
            "avatar_url":user[7],
            "bio": user[8],
        }

    async def get_id_by_username(self,username: str) -> UserId :
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user = await cursor.fetchone()
        if user is None:
            raise NotFoundException(detail="User not found")
        return {"id":user[0]}

    async def patch_user(self,id:str, data: UpdateUser):
        conn = get_db_connection()
        cursor = conn.cursor()
        data = data.model_dump() if isinstance(data, UpdateUser) else data
        async with self.db.transaction():
            async with self.db.cursor() as cursor:
                await cursor.execute(f"UPDATE users SET {data["field"]} = %s WHERE id = %s;", (data["value"], id))

    async def get_favorite_user(self, user_id:int):
        try:
            async with self.db.cursor() as cursor:
                await cursor.execute(f"SELECT c.id, c.nom, m.id, m.nom, cat.id, cat.nom,uf.type_id,type.type FROM user_favorites uf LEFT JOIN concepts c ON uf.concept_id = c.id LEFT JOIN mathematiciens m ON uf.mathematicien_id = m.id LEFT JOIN categories cat ON uf.category_id = cat.id LEFT JOIN type ON uf.type_id=type.id WHERE uf.user_id = %s ;", (user_id,))
                favorite = await cursor.fetchall()
            if favorite is None:
                return None
            dictList=[]
            for elt in favorite:
                if elt[0] is not None:
                    dictList.append(
                        {
                            "id":elt[0],
                            "nom":elt[1],
                            "category":"concept"
                        }
                    )
                elif elt[2] is not None:
                    dictList.append(
                        {
                            "id":elt[2],
                            "nom":elt[3],
                            "category":"mathematicien"
                        }
                    )
                elif elt[4] is not None:
                    dictList.append(
                        {
                            "id":elt[4],
                            "nom":elt[5],
                            "category":"category"
                        }
                    )
                elif elt[6] is not None:
                    dictList.append(
                        {
                            "id":elt[6],
                            "type":elt[7],
                            "category":"type"
                        }
                    )


            return dictList

        except Exception as e:
            print(f"Erreur a l'obtention des favoris : {e}")
            return None

    async def delete_favorite_user(self,general_id:int, data:Favorite):
        data = data.model_dump() if isinstance(data, Favorite) else data
        try:
            async with self.db.transaction():
                async with self.db.cursor() as cursor:
                    if data["type"] == "concept":
                        await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND concept_id = %s;", (data["user_id"],general_id))
                    elif data["type"] == "mathematicien":
                        await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND mathematicien_id = %s;", (data["user_id"],general_id))
                    elif data["type"] == "category":
                        await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND category_id = %s;", (data["user_id"],general_id))
                    elif data["type"] == "type":
                        await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND type_id = %s;", (data["user_id"],general_id))
        except Exception as e:
            raise InternalServerError(detail=e)


    async def add_favorite_user(self,general_id:int, data:Favorite):
        data = data.model_dump() if isinstance(data, Favorite) else data
        data["user_id"]=int(data["user_id"])
        try:
            async with self.db.transaction():
                async with self.db.cursor() as cursor:
                    if data["type"] == "concept":
                        print("ues")
                        await cursor.execute(f"INSERT INTO user_favorites (user_id, concept_id) VALUES (%s, %s);", (data["user_id"],general_id))
                    elif data["type"] == "mathematicien":
                        await cursor.execute(f"INSERT INTO user_favorites (user_id, mathematicien_id) VALUES (%s, %s);", (data["user_id"],general_id))
                    elif data["type"] == "category":
                        await cursor.execute(f"INSERT INTO user_favorites (user_id, category_id) VALUES (%s, %s);", (data["user_id"],general_id))
                    elif data["type"] == "type":
                        await cursor.execute(f"INSERT INTO user_favorites (user_id, type_id) VALUES (%s, %s);", (data["user_id"],general_id))
        except Exception as e:
            raise InternalServerError(detail=e)
