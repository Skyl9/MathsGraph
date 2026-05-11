from datetime import datetime

from psycopg import AsyncConnection

from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.user import UserId, UpdateUser, Favorite
from app.utils.db_utils import get_id_by_field

import logging

logger = logging.getLogger(__name__)


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
        user_id = await get_id_by_field(self.db, "users", "username", username, "User not found")
        return {"id": user_id}

    async def patch_user(self,id:str, data: UpdateUser) -> None:
        data = data.model_dump() if isinstance(data, UpdateUser) else data
        allowed_fields = {"username", "email", "is_active", "role", "preferred_language", "avatar_url", "bio"}
        field:str = data["field"]
        if field not in allowed_fields:
            raise BadRequestException(detail="Mauvais champ donné")

        await get_id_by_field(self.db, "users", "id", id, "User not found")

        async with self.db.cursor() as cursor:
            await cursor.execute(f"UPDATE users SET {field} = %s WHERE id = %s;", (data["value"], id))

    async def get_favorite_user(self, user_id:int):
            await get_id_by_field(self.db, "users", "id", user_id, "User not found")
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

    async def delete_favorite_user(self,general_id:int, data:Favorite) -> None:
        data = data.model_dump() if isinstance(data, Favorite) else data

        await get_id_by_field(self.db, "users", "id", data["user_id"], "User not found")
        await get_id_by_field(self.db, "concepts", "id", general_id, "Concept not found")

        async with self.db.cursor() as cursor:
            if data["type"] == "concept":
                await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND concept_id = %s;", (data["user_id"],general_id))
            elif data["type"] == "mathematicien":
                await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND mathematicien_id = %s;", (data["user_id"],general_id))
            elif data["type"] == "category":
                await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND category_id = %s;", (data["user_id"],general_id))
            elif data["type"] == "type":
                await cursor.execute(f"DELETE FROM user_favorites WHERE user_id = %s AND type_id = %s;", (data["user_id"],general_id))



    async def add_favorite_user(self,general_id:int, data:Favorite)->None:
        data = data.model_dump() if isinstance(data, Favorite) else data
        data["user_id"]=int(data["user_id"])

        await get_id_by_field(self.db, "users", "id", data["user_id"], "User not found")
        await get_id_by_field(self.db, "concepts", "id", general_id, "Concept not found")

        async with self.db.cursor() as cursor:
            if data["type"] == "concept":
                await cursor.execute(f"INSERT INTO user_favorites (user_id, concept_id) VALUES (%s, %s);", (data["user_id"],general_id))
            elif data["type"] == "mathematicien":
                await cursor.execute(f"INSERT INTO user_favorites (user_id, mathematicien_id) VALUES (%s, %s);", (data["user_id"],general_id))
            elif data["type"] == "category":
                await cursor.execute(f"INSERT INTO user_favorites (user_id, category_id) VALUES (%s, %s);", (data["user_id"],general_id))
            elif data["type"] == "type":
                await cursor.execute(f"INSERT INTO user_favorites (user_id, type_id) VALUES (%s, %s);", (data["user_id"],general_id))

