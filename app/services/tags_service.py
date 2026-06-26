import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db_utils import get_id_by_field
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.db.models import Tag
from app.repositories.tags_repository import TagsRepository
from app.core.security import verify_admin_moderator

logger = logging.getLogger(__name__)


class TagsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TagsRepository(db)

    async def get_tags_id_by_concept_id(self, concept_id: int, warning=True) -> List[int] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")

        tags = await self.repo.get_tags_id_by_concept_id(concept_id)

        if not tags:
            if warning:
                raise NotFoundException(f"No tags found for this concept id: {concept_id}")
            else:
                return None
        return list(tags)

    async def get_tags_name_and_id_by_concept_id(self, concept_id: int, warning=True) -> List[dict] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")

        tags = await self.repo.get_tags_name_and_id_by_concept_id(concept_id)

        if not tags:
            if warning:
                raise NotFoundException(f"No tags found for this concept id: {concept_id}")
            else:
                return None
        return [{"id": tag.id, "tag": tag.name} for tag in tags]

    async def get_all_tags(self) -> List[dict] | None:
        tags = await self.repo.get_all()
        return [{"id": tag.id, "tag": tag.name} for tag in tags]

    async def create_new_tag(self, tag_name: str, current_user: dict) -> None:
        verify_admin_moderator(current_user)

        existing = await self.repo.get_tag_by_name(tag_name)
        if existing:
            raise ConflictException(detail="Tag already exists")

        new_tag = Tag(name=tag_name)
        await self.repo.add(new_tag)

    async def add_tag_to_concept(self, concept_id: int, tag_id: int, current_user: dict) -> None:
        verify_admin_moderator(current_user)

        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")

        relation = await self.repo.check_concept_tag_relation(concept_id, tag_id)
        if relation:
            raise BadRequestException(detail="Relation already exists for this concept and tag")

        await self.repo.add_tag_to_concept(concept_id, tag_id)

    async def remove_tag_from_concept(self, concept_id: int, tag_id: int, current_user: dict) -> None:
        verify_admin_moderator(current_user)

        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")

        relation = await self.repo.check_concept_tag_relation(concept_id, tag_id)
        if not relation:
            raise BadRequestException(detail="Relation does not exist for this concept and tag")

        await self.repo.remove_tag_from_concept(concept_id, tag_id)
