from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException


async def check_exists(db: AsyncSession, table_name: str, entity_id: int, error_msg: str = "Ressource introuvable"):
    """Vérifie si un ID existe dans une table spécifique, sinon lève une NotFoundException."""
    # Note: Using text() for dynamic table names is generally risky,
    # but here we follow the existing pattern while migrating to AsyncSession.
    query = text(f"SELECT id FROM {table_name} WHERE id = :id LIMIT 1")
    result = await db.execute(query, {"id": entity_id})
    if result.scalar_one_or_none() is None:
        raise NotFoundException(detail=error_msg)


async def get_id_by_field(
    db: AsyncSession, table_name: str, field_name: str, field_value: Any, error_msg: str = "Ressource introuvable"
) -> int:
    """
    Cherche un enregistrement via un champ spécifique et retourne son ID.
    Lève une NotFoundException si l'enregistrement n'existe pas.
    """
    if not field_value:
        raise NotFoundException(detail=error_msg)

    query = text(f"SELECT id FROM {table_name} WHERE {field_name} = :val LIMIT 1")
    result = await db.execute(query, {"val": field_value})
    row = result.fetchone()

    if row is None:
        raise NotFoundException(detail=error_msg)

    return int(row[0])
