from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import Concept, Relation


class RelationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_concept_id_by_name(self, name: str):
        query = select(Concept.id).where(func.trim(Concept.nom) == name.strip())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_relation_id(self, source_id: int, cible_id: int):
        query_rel = select(Relation.id).where(Relation.concept_source == source_id, Relation.concept_cible == cible_id)
        res_rel = await self.db.execute(query_rel)
        return res_rel.scalar_one_or_none()

    async def add(self, relation: Relation):
        self.db.add(relation)
        await self.db.flush()
