import logging

from psycopg import AsyncConnection, sql

from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.schemas import CreateData
from app.schemas.categorie import CategorieBase, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def get_all_categories(self) -> list[CategorieBase]:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT id, nom, description, parent_id FROM categories;"
            )
            rows = await cur.fetchall()
        return [
            {
                "id": row[0],
                "nom": row[1],
                "description": row[2],
                "parent_id": row[3],
            }
            for row in rows
        ]

    async def get_one_category(self, id_category: int) -> CategorieBase:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT id, nom, description, parent_id FROM categories WHERE id = %s;",
                (id_category,),
            )
            row = await cur.fetchone()

        if not row:
            raise NotFoundException(detail=f"Category {id_category} not found")

        return {
            "id": row[0],
            "nom": row[1],
            "description": row[2],
            "parent_id": row[3],
        }

    async def update_category(self, id_category: int, data: CategoryUpdate) -> None:
        allowed_fields = {"nom", "description", "parent_id"}
        data = data.model_dump() if isinstance(data, CategoryUpdate) else data
        field = data["field"]  # si CategoryUpdate hérite de BaseModel
        if field not in allowed_fields:
            raise ForbiddenException(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        query = sql.SQL(f"UPDATE categories SET {field} = %s WHERE id = %s").format(
            field=sql.Identifier(field)
        )
        async with self.db.cursor() as cur:
            await cur.execute(query, (data["value"], id_category))

    async def add_category(self, data: CreateData) -> None:
        payload = data.model_dump() if isinstance(data, CreateData) else data
        nom = payload["value"]
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT id FROM categories WHERE nom = %s;", (nom,)
            )
            if await cur.fetchone() is not None:
                raise ConflictException(detail=f"Category {nom} already exists")

            await cur.execute(
                "INSERT INTO categories (nom) VALUES (%s);", (nom,)
            )

    async def get_category_id_by_name(self, name: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT id FROM categories WHERE nom = %s;", (name,)
            )
            row = await cur.fetchone()

        if row is None:
            return None
        return {"id": row[0], "nom": name}
