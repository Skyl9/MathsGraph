import logging
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, BadRequestException
from app.schemas import CreateSource
from app.utils.db_utils import get_id_by_field
from app.db.models import Source, concepts_sources

logger = logging.getLogger(__name__)


class SourceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_source(self, data: CreateSource):
        data_dict = data.model_dump() if isinstance(data, CreateSource) else data
        val = data_dict["value"]

        allowed_types = ["article", "livre", "site_web", "autre"]
        if val["type"] not in allowed_types:
            raise BadRequestException(detail="Type not allowed")

        # Vérifier que le concept existe
        await get_id_by_field(self.db, "concepts", "id", val["id"], "Concept not found")

        # Vérifier si la source existe déjà
        query_src = select(Source.id).where(Source.titre == val["source"])
        res_src = await self.db.execute(query_src)
        if res_src.scalar_one_or_none() is not None:
            raise ConflictException(detail="Source already exists")

        # Créer la source
        new_source = Source(
            titre=val["source"], auteur=val["auteur"], annee=val["annee"], url=val["url"], type=val["type"]
        )
        self.db.add(new_source)
        await self.db.flush()

        # Lier la source au concept
        stmt = insert(concepts_sources).values(concept_id=val["id"], source_id=new_source.id)
        await self.db.execute(stmt)
        await self.db.flush()
