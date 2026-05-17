import logging
from typing import List
from sqlalchemy import select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.db_utils import get_id_by_field
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.schemas.tags import Tag as TagSchema
from app.db.models import Tag, Concept, concept_tags

logger = logging.getLogger(__name__)


class TagsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tags_id_by_concept_id(self, concept_id: int, warning=True) -> List[int] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        
        query = select(concept_tags.c.tag_id).where(concept_tags.c.concept_id == concept_id)
        result = await self.db.execute(query)
        tags = result.scalars().all()
        
        if not tags:
            if warning:
                raise NotFoundException(f"No tags found for this concept id: {concept_id}")
            else:
                return None
        return list(tags)

    async def get_tags_name_and_id_by_concept_id(self, concept_id: int, warning=True) -> List[dict] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        
        query = (
            select(Tag.id, Tag.name)
            .join(concept_tags, concept_tags.c.tag_id == Tag.id)
            .where(concept_tags.c.concept_id == concept_id)
        )
        result = await self.db.execute(query)
        tags = result.all()
        
        if not tags:
            if warning:
                raise NotFoundException(f"No tags found for this concept id: {concept_id}")
            else:
                return None
        return [{"id": tag.id, "tag": tag.name} for tag in tags]

    async def get_all_tags(self) -> List[dict] | None:
        query = select(Tag.id, Tag.name)
        result = await self.db.execute(query)
        tags = result.all()
        return [{"id": tag.id, "tag": tag.name} for tag in tags]

    async def create_new_tag(self, tag_name: str) -> None:
        query = select(Tag).where(Tag.name == tag_name)
        result = await self.db.execute(query)
        if result.scalars().first():
            raise ConflictException(detail="Tag already exists")
            
        new_tag = Tag(name=tag_name)
        self.db.add(new_tag)
        await self.db.flush()

    async def add_tag_to_concept(self, concept_id: int, tag_id: int) -> None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")

        query = select(concept_tags.c.concept_id).where(
            concept_tags.c.concept_id == concept_id,
            concept_tags.c.tag_id == tag_id
        )
        result = await self.db.execute(query)
        if result.scalars().first():
            raise BadRequestException(detail="Relation already exists for this concept and tag")
            
        stmt = insert(concept_tags).values(concept_id=concept_id, tag_id=tag_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def remove_tag_from_concept(self, concept_id: int, tag_id: int) -> None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")

        query = select(concept_tags.c.concept_id).where(
            concept_tags.c.concept_id == concept_id,
            concept_tags.c.tag_id == tag_id
        )
        result = await self.db.execute(query)
        if not result.scalars().first():
            raise BadRequestException(detail="Relation does not exist for this concept and tag")
            
        stmt = delete(concept_tags).where(
            concept_tags.c.concept_id == concept_id,
            concept_tags.c.tag_id == tag_id
        )
        await self.db.execute(stmt)
        await self.db.flush()
