from psycopg import AsyncConnection

from app.core.exceptions import ConflictException, NotFoundException, BadRequestException
from app.schemas import CreateSource
from app.utils.db_utils import get_id_by_field
import logging

logger = logging.getLogger(__name__)

class SourceService:
    def __init__(self,db:AsyncConnection):
        self.db = db
    async def create_source(self,data: CreateSource):
        data = data.model_dump() if isinstance(data, CreateSource) else data
        data = data["value"]
        allowed_types = ["article", "livre","site_web","autre"]
        if data["type"] not in allowed_types:
            raise BadRequestException(detail="Type not allowed")

        await get_id_by_field(self.db, "concepts", "id", data["id"], "Concept not found")

        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT id FROM sources WHERE titre = %s;", (data["source"],))
            if await cursor.fetchone() is not None:
                raise ConflictException(detail="Source already exists")
            await cursor.execute("INSERT INTO sources (titre,auteur,annee,url,type) VALUES  (%s,%s,%s,%s,%s) RETURNING id;",
                           (data["source"], data["auteur"], data["annee"], data["url"], data["type"]))
            source_id = (await cursor.fetchone())[0]
            await cursor.execute("INSERT INTO concepts_sources (concept_id, source_id) VALUES  (%s,%s);", (data["id"], source_id))
