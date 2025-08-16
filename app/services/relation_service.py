from psycopg import AsyncConnection

from app.core.exceptions import ConflictException, NotFoundException
from app.schemas import CreateRelation

import logging

logger = logging.getLogger(__name__)


class RelationService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def add_relation(self, data: CreateRelation):
        data = data.model_dump() if isinstance(data, CreateRelation) else data
        data = data["value"]
        async with self.db.cursor() as cursor:

            await cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo1"],))
            theo1 = await cursor.fetchone()
            theo1 = theo1[0] if theo1 else None
            await cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo2"],))
            theo2 = await cursor.fetchone()
            theo2 = theo2[0] if theo2 else None

            if theo1 is None or theo2 is None:
                raise NotFoundException(detail="Concept not found")
            if theo1 == theo2:
                raise ConflictException(detail="Concept cannot be related to itself")

            await cursor.execute("SELECT id FROM relations WHERE concept_source = %s AND concept_cible = %s;",
                                 (theo1, theo2))

            if await cursor.fetchone() is not None:
                raise ConflictException(detail="Relation already exists")


            await cursor.execute(
                "INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES  (%s,%s,%s,%s);",
                (theo1, theo2, data["relation"], data["desc"]))
