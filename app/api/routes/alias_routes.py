from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import CreateAlias, Response
from app.services.alias_service import AliasService, logger

router = APIRouter(prefix="/alias", tags=["alias"])


@router.post("", response_model=Response)
async def create_alias(
    data: CreateAlias, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    """Crée un alias à partir d'un nom d'utilisateur et d'un prénom."""
    await AliasService(db).add_alias(data)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/alias : {str(data)} ")
    return {"success": True, "data": None, "meta": None, "error": None}
