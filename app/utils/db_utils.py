from typing import Any

from psycopg import AsyncConnection
from psycopg import sql
from app.core.exceptions import NotFoundException

async def check_exists(db: AsyncConnection, table_name: str,entity_id: int, error_msg: str = "Ressource introuvable"):
    """Vérifie si un ID existe dans une table spécifique, sinon lève une NotFoundException."""
    async with db.cursor() as cursor:
        query = sql.SQL("SELECT id FROM {} WHERE id = %s LIMIT 1;").format(sql.Identifier(table_name))
        await cursor.execute(query, (entity_id,))
        if await cursor.fetchone() is None:
            raise NotFoundException(detail=error_msg)


async def get_id_by_field(
        db: AsyncConnection,
        table_name: str,
        field_name: str,
        field_value: Any,
        error_msg: str = "Ressource introuvable"
) -> int:
    """
    Cherche un enregistrement via un champ spécifique et retourne son ID.
    Lève une NotFoundException si l'enregistrement n'existe pas.
    """
    if not field_value:
        raise NotFoundException(detail=error_msg)

    async with db.cursor() as cursor:
        # Construction sécurisée de la requête dynamique avec psycopg.sql
        query = sql.SQL("SELECT id FROM {} WHERE {} = %s LIMIT 1;").format(
            sql.Identifier(table_name),
            sql.Identifier(field_name)
        )

        await cursor.execute(query, (field_value,))
        result = await cursor.fetchone()

        if result is None:
            raise NotFoundException(detail=error_msg)

        return result[0]