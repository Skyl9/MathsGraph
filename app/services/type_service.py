from fastapi import HTTPException
from psycopg import AsyncConnection
from psycopg2 import sql

from app.core.exceptions import NotFoundException, InternalServerError, ForbiddenException, ConflictException
from app.db.database import get_db_connection
from app.schemas import CreateData
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom

import logging

logger = logging.getLogger(__name__)

class TypeService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_all_type_name(self) -> list[TypeNom]:
        try:
            async with self.db.cursor() as cur:
                await cur.execute("SELECT id, type FROM type")
                types_fetched = await cur.fetchall()
            return [{"id": i[0], "type": i[1]} for i in types_fetched]
        except Exception as e:
            raise InternalServerError(detail=e)


    async def get_one_type(self,id_type: int) -> TypeResponse:
        try:
            async with self.db.cursor() as cur:
                await cur.execute("SELECT * FROM type WHERE id = %s", (id_type,))
                type_fetched = await cur.fetchone()
            if not type_fetched:
                raise NotFoundException(f"Type with ID {id_type} not found")
            return {
                "id": type_fetched[0],
                "type": type_fetched[1],
            }
        except Exception as e:
            raise InternalServerError(detail=e)

    async def update_type(self,id_type: int, data: TypeUpdate):
        allowed_fields = {"type"}
        field = data["field"]

        if field not in allowed_fields:
            raise ForbiddenException(
                f"Le champ '{field}' n'est pas autorisé pour une mise à jour."
            )

        try:
            async with self.db.transaction():
                async with self.db.cursor() as cur:
                    query = sql.SQL(f"UPDATE type SET {field} = %s WHERE id = %s").format(
                        field=sql.Identifier(field)
                    )
                    await cur.execute(query, (data["value"], id_type))
        except Exception as e:
            raise InternalServerError(detail=e)

    async def add_type(self,data: CreateData):


        data = data.model_dump() if isinstance(data, CreateData) else data
        async with self.db.transaction():
            async with self.db.cursor() as cursor:
                await cursor.execute("SELECT id FROM type WHERE type = %s;", (data["value"],))

                if await cursor.fetchone() is not None:
                    raise ConflictException(detail="Type already exists")
                await cursor.execute("INSERT INTO type (type) VALUES  (%s);", (data["value"],))



    async def get_category_id(self,nom):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT id FROM type WHERE type.type = %s;", (nom,))
            type = await cursor.fetchone()
            if type is None:
                return None
        return {"id":type[0],"type":nom}