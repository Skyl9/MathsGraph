from fastapi import APIRouter, Depends, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import Response
from app.services.statistics_service import StatisticsService, logger

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "/concepts/{concept_id}",
    summary="Récupère les statistiques de vues d'un concept",
    description="Permet de récupérer le nombre total de vues pour un concept spécifique en fournissant son identifiant.",
    response_model=Response,
)
async def get_concept_views(concept_id: int, db: AsyncSession = Depends(get_db)):
    views = await StatisticsService(db).get_concept_views(concept_id)
    logger.debug(f"Route GET {router.prefix}/concepts/{concept_id} a renvoyé correctement : <data_omitted>")
    return {"error": None, "data": views, "success": True, "meta": None}


@router.post(
    "/concepts/{concept_id}",
    summary="Enregistre une vue pour un concept",
    description="Enregistre une nouvelle vue sur un concept. Cette route capture l'adresse IP du client et l'identifiant de l'utilisateur s'il est connecté, afin de suivre les statistiques de consultation.",
    response_model=Response,
)
async def add_concept_view(
    concept_id: int,
    request: Request,
    user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip_address = request.client.host if request.client else None
    user_id = user.id if user else None

    result = await StatisticsService(db).add_concept_view(concept_id, user_id, ip_address)
    logger.debug(f"Route POST {router.prefix}/concepts/{concept_id} a enregistré une vue.")
    return {"error": None, "data": result, "success": True, "meta": None}
