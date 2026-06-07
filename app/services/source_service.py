import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, BadRequestException
from app.schemas import CreateSource
from app.utils.db_utils import get_id_by_field
from app.db.models import Source
from app.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class SourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SourceRepository(db)

    async def create_source(self, data: CreateSource):
        data_dict = data.model_dump() if isinstance(data, CreateSource) else data
        val = data_dict["value"]

        allowed_types = ["article", "livre", "site_web", "autre"]
        if val["type"] not in allowed_types:
            raise BadRequestException(detail="Type not allowed")

        # Vérifier que le concept existe
        await get_id_by_field(self.db, "concepts", "id", val["id"], "Concept not found")

        # Vérifier si la source existe déjà
        src_id = await self.repo.get_source_id_by_title(val["source"])
        if src_id is not None:
            raise ConflictException(detail="Source already exists")

        # Créer la source
        new_source = Source(
            titre=val["source"], auteur=val["auteur"], annee=val["annee"], url=val["url"], type=val["type"]
        )
        await self.repo.add(new_source)

        # Lier la source au concept
        await self.repo.link_concept_source(val["id"], new_source.id)
