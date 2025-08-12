from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response
from app.services.statistics_service import StatisticsService, logger

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/concepts/{concept_id}", summary="Récupère les statistiques de vues d'un concept", response_model=Response)
async def get_concept_views(concept_id: int, db: AsyncConnection = Depends(get_db)):
    try:
        views = await StatisticsService(db).get_concept_views(concept_id)
        logger.debug(f'Route GET /{router.prefix}/concepts/{concept_id} a renvoyé correctement : {views}')
        return {"error": None, "data": views, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /statistics/concepts/{concept_id} Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc