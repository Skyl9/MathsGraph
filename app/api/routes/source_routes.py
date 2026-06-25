from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, CreateSource
from app.services.source_service import SourceService, logger

router = APIRouter(prefix="/source", tags=["source"])


@router.post(
    "",
    summary="Crée une nouvelle source",
    description="Permet de créer une nouvelle source bibliographique ou documentaire dans la base de données. L'utilisateur doit être authentifié.",
    response_model=Response,
)
async def create_source(
    data: CreateSource, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await SourceService(db).create_source(data)
    await db.commit()
    logger.debug("Route POST /source a correctement créé une source")
    return {"error": None, "data": None, "success": True, "meta": None}
