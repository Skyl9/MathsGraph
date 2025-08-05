from fastapi import HTTPException
from psycopg import AsyncConnection

from app.db.database import get_db_connection
from app.schemas import CreateSource


class SourceService:
    def __init__(self,db:AsyncConnection):
        self.db = db
    async def create_source(self,data: CreateSource):
        data = data.model_dump() if isinstance(data, CreateSource) else data
        data = data["value"]
        async with self.db.transaction():
            async with self.db.cursor() as cursor:
                await cursor.execute("SELECT id FROM sources WHERE titre = %s;", (data["source"],))
                if await cursor.fetchone() is not None:
                    raise HTTPException(status_code=409, detail="Source already exists")
                await cursor.execute("INSERT INTO sources (titre,auteur,annee,url,type) VALUES  (%s,%s,%s,%s,%s) RETURNING id;",
                               (data["source"], data["auteur"], data["annee"], data["url"], data["type"]))
                source_id = cursor.fetchone()[0]
                await cursor.execute("INSERT INTO concepts_sources (concept_id, source_id) VALUES  (%s,%s);", (data["id"], source_id))
