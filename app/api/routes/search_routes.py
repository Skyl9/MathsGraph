from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.search import AdvancedSearchPayload
from app.db.database import get_db
from app.services.search_service import SearchService
from app.schemas import Response

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/quick",
    summary="Recherche globale rapide",
    description="Effectue une recherche textuelle rapide sur l'ensemble des concepts, mathématiciens, sources et domaines. Nécessite au moins 2 caractères.",
    response_model=Response,
)
async def quick_search(q: str, db: AsyncSession = Depends(get_db)):
    if len(q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    results = await SearchService(db).global_quick_search(q)
    return {"success": True, "data": results, "error": None, "meta": None}


@router.post(
    "/advanced",
    summary="Recherche avancée",
    description="Effectue une recherche textuelle avancée en appliquant des filtres spécifiques de catégories. Nécessite au moins 2 caractères.",
    response_model=Response,
)
async def advanced_search(payload: AdvancedSearchPayload, db: AsyncSession = Depends(get_db)):
    if len(payload.q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    results = await SearchService(db).advanced_search(payload.q, payload.filters)
    return {"success": True, "data": results, "error": None, "meta": None}
