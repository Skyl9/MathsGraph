import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ConflictException
from app.schemas import CreateAlias
from app.db.models import Alias

logger = logging.getLogger(__name__)


class AliasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_alias(self, data: CreateAlias):
        data_dict = data.model_dump() if isinstance(data, CreateAlias) else data
        
        # Vérifier si l'alias existe déjà
        query = select(Alias).where(Alias.alias == data_dict["value"])
        result = await self.db.execute(query)
        if result.scalars().first() is not None:
            logger.warning(f"Alias {data_dict['value']} already exists")
            raise ConflictException(detail="Alias already exists")
            
        new_alias = Alias(concept_id=data_dict["id"], alias=data_dict["value"])
        self.db.add(new_alias)
        await self.db.flush()
        
        return {"id": new_alias.id, "alias": new_alias.alias}
