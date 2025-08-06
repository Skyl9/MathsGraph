from psycopg import AsyncConnection

from app.core.exceptions import ConflictException
from app.schemas import CreateAlias


class AliasService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def add_alias(self, data: CreateAlias):
        data = data.model_dump() if isinstance(data, CreateAlias) else data
        async with self.db.transaction():
            async with self.db.cursor() as cursor:
                await cursor.execute("SELECT id FROM aliases WHERE alias = %s;", (data["value"],))
                if await cursor.fetchone() is not None:
                    raise ConflictException(detail="Alias already exists")
                await cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES  (%s,%s) RETURNING  id;", (data["id"], data["value"]))
                row = await cursor.fetchone()
                new_id = row[0]
        return {"id": new_id, "alias": data["value"]}
