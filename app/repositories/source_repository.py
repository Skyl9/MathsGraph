from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.db.models import Source, concepts_sources


class SourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_source_id_by_title(self, title: str):
        query_src = select(Source.id).where(Source.titre == title)
        res_src = await self.db.execute(query_src)
        return res_src.scalar_one_or_none()

    async def add(self, source: Source):
        self.db.add(source)
        await self.db.flush()
        return source

    async def link_concept_source(self, concept_id: int, source_id: int):
        stmt = insert(concepts_sources).values(concept_id=concept_id, source_id=source_id)
        await self.db.execute(stmt)
        await self.db.flush()
