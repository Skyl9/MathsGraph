from app.core.limiter import limiter
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import CreateAlias, Response
from app.services.alias_service import AliasService, logger

router = APIRouter(prefix="/aliases", tags=["alias"])


@router.post(
    "",
    status_code=201,
    response_model=Response,
    summary="Création d'un alias",
    description="Permet de créer un nouvel alias associé à un utilisateur. L'utilisateur doit être authentifié.",
)
@limiter.limit("20/minute")
async def create_alias(
    request: Request,
    data: CreateAlias,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    """Crée un alias à partir d'un nom d'utilisateur et d'un prénom."""
    await AliasService(db).add_alias(data)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/alias a été appelée avec succès")
    return {"success": True, "data": None, "meta": None, "error": None}
