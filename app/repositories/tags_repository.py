from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.db.models import Tag, concept_tags


class TagsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tags_id_by_concept_id(self, concept_id: int):
        query = select(concept_tags.c.tag_id).where(concept_tags.c.concept_id == concept_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_tags_name_and_id_by_concept_id(self, concept_id: int):
        query = (
            select(Tag.id, Tag.name)
            .join(concept_tags, concept_tags.c.tag_id == Tag.id)
            .where(concept_tags.c.concept_id == concept_id)
        )
        result = await self.db.execute(query)
        return result.all()

    async def get_all_tags(self):
        query = select(Tag.id, Tag.name)
        result = await self.db.execute(query)
        return result.all()

    async def get_tag_by_name(self, tag_name: str):
        query = select(Tag).where(Tag.name == tag_name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add_tag(self, tag: Tag):
        self.db.add(tag)
        await self.db.flush()

    async def check_concept_tag_relation(self, concept_id: int, tag_id: int):
        query = select(concept_tags.c.concept_id).where(
            concept_tags.c.concept_id == concept_id, concept_tags.c.tag_id == tag_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add_tag_to_concept(self, concept_id: int, tag_id: int):
        stmt = insert(concept_tags).values(concept_id=concept_id, tag_id=tag_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def remove_tag_from_concept(self, concept_id: int, tag_id: int):
        stmt = delete(concept_tags).where(concept_tags.c.concept_id == concept_id, concept_tags.c.tag_id == tag_id)
        await self.db.execute(stmt)
        await self.db.flush()
