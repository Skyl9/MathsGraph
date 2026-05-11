import logging
from typing import List

from psycopg import AsyncConnection
from app.utils.db_utils import get_id_by_field

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.schemas.tags import Tag

logger = logging.getLogger(__name__)


class TagsService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def get_tags_id_by_concept_id(self, concept_id: int, warning=True) -> List[int] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT tag_id FROM concept_tags WHERE concept_id = %s;", (concept_id,)
            )
            tags = await cursor.fetchall()
        if not tags:
            if warning:
                raise NotFoundException(f"No tags found for this concept id: {concept_id}")
            else:
                return None
        return [tag[0] for tag in tags]

    async def get_tags_name_and_id_by_concept_id(self, concept_id: int, warning=True) -> List[Tag] | None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT concept_tags.tag_id, tags.name FROM concept_tags JOIN tags ON concept_tags.tag_id = tags.id WHERE concept_id = %s;",
                (concept_id,)
            )
            tags = await cursor.fetchall()
            if not tags:
                if warning:
                    raise NotFoundException(f"No tags found for this concept id: {concept_id}")
                else:
                    return None
        return [{"id": tag[0], "tag": tag[1]} for tag in tags]

    async def get_all_tags(self) -> List[Tag] | None:
        async  with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT id, name FROM tags;"
            )
            tags = await cursor.fetchall()
            tags = [{"id": tag[0], "tag": tag[1]} for tag in tags]
        return tags


    async def create_new_tag(self, tag_name: str) -> None:
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT name FROM tags WHERE name = %s;", (tag_name,))
            if await cursor.fetchone():
                raise ConflictException(detail="Tag already exists")
            await cursor.execute(
                "INSERT INTO tags (name) VALUES (%s);", (tag_name,)
            )

    async def add_tag_to_concept(self, concept_id: int, tag_id: int) -> None:
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")

        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT concept_id FROM concept_tags WHERE concept_id = %s AND tag_id = %s;",
                                 (concept_id, tag_id))
            if await cursor.fetchone():
                raise BadRequestException(detail="Relation already exists for this concept and tag")
            await cursor.execute(
                "INSERT INTO concept_tags (concept_id, tag_id) VALUES (%s, %s);", (concept_id, tag_id)
            )

    async def remove_tag_from_concept(self, concept_id: int, tag_id: int) -> None:
        await get_id_by_field(self.db, "tags", "id", tag_id, "Tag introuvable")
        await get_id_by_field(self.db, "concepts", "id", concept_id, "Concept introuvable")

        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT concept_id FROM concept_tags WHERE concept_id = %s AND tag_id = %s;",
                                 (concept_id, tag_id))
            if not await cursor.fetchone():
                raise BadRequestException(detail="Relation does not exist for this concept and tag")
            await cursor.execute(
                "DELETE FROM concept_tags WHERE concept_id = %s AND tag_id = %s;", (concept_id, tag_id)
            )
