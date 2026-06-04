from typing import Any
from sqlalchemy import select, table, column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException


async def check_exists(db: AsyncSession, table_name: str, entity_id: int, error_msg: str = "Ressource introuvable"):
    """Vérifie si un ID existe dans une table spécifique, sinon lève une NotFoundException."""
    t = table(table_name, column("id"))
    query = select(t.c.id).where(t.c.id == entity_id).limit(1)
    result = await db.execute(query)
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

    t = table(table_name, column("id"), column(field_name))
    query = select(t.c.id).where(getattr(t.c, field_name) == field_value).limit(1)
    result = await db.execute(query)
    row = result.fetchone()

    if row is None:
        raise NotFoundException(detail=error_msg)

    return int(row[0])
