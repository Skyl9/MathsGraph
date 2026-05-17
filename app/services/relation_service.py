import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.schemas import CreateRelation
from app.db.models import Concept, Relation

logger = logging.getLogger(__name__)


class RelationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_relation(self, data: CreateRelation):
        data_dict = data.model_dump() if isinstance(data, CreateRelation) else data
        val = data_dict["value"]
        
        # Récupérer les IDs des concepts
        query1 = select(Concept.id).where(func.trim(Concept.nom) == val["théo1"].strip())
        res1 = await self.db.execute(query1)
        theo1 = res1.scalar_one_or_none()
        
        query2 = select(Concept.id).where(func.trim(Concept.nom) == val["théo2"].strip())
        res2 = await self.db.execute(query2)
        theo2 = res2.scalar_one_or_none()

        if theo1 is None or theo2 is None:
            raise NotFoundException(detail="Concept not found")
        if theo1 == theo2:
            raise ConflictException(detail="Concept cannot be related to itself")

        # Vérifier si la relation existe déjà
        query_rel = select(Relation.id).where(
            Relation.concept_source == theo1,
            Relation.concept_cible == theo2
        )
        res_rel = await self.db.execute(query_rel)
        if res_rel.scalar_one_or_none() is not None:
            raise ConflictException(detail="Relation already exists")

        new_rel = Relation(
            concept_source=theo1,
            concept_cible=theo2,
            type_relation=val["relation"],
            description=val["desc"]
        )
        self.db.add(new_rel)
        await self.db.flush()
