from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, CreateRelation
from app.services.relation_service import RelationService, logger

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post(
    "",
    summary="Crée une nouvelle relation",
    description="Permet de créer une nouvelle relation entre deux entités (concepts). L'utilisateur doit être authentifié pour effectuer cette action.",
    response_model=Response,
)
async def create_relation(
    data: CreateRelation, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await RelationService(db).add_relation(data)
    await db.commit()
    logger.debug("Route POST /relation a correctement créé une relation")
    return {"error": None, "data": None, "success": True, "meta": None}
