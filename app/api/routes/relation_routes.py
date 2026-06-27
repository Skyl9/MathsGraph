from app.core.limiter import limiter
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, CreateRelation
from app.services.relation_service import RelationService, logger

router = APIRouter(prefix="/relations", tags=["relation"])


@router.post(
    "",
    status_code=201,
    summary="Crée une nouvelle relation",
    description="Permet de créer une nouvelle relation entre deux entités (concepts). L'utilisateur doit être authentifié pour effectuer cette action.",
    response_model=Response,
)
@limiter.limit("20/minute")
async def create_relation(
    request: Request,
    data: CreateRelation,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await RelationService(db).add_relation(data)
    await db.commit()
    logger.debug("Route POST /relation a correctement créé une relation")
    return {"error": None, "data": None, "success": True, "meta": None}
