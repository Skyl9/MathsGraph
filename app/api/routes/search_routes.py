from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.search import AdvancedSearchPayload
from app.db.database import get_db
from app.services.search_service import SearchService
from app.schemas import Response
from app.core.redis_client import redis_db
from app.core.limiter import limiter
from fastapi.encoders import jsonable_encoder
import json

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/quick",
    summary="Recherche globale rapide",
    description="Effectue une recherche textuelle rapide sur l'ensemble des concepts, mathématiciens, sources et domaines. Nécessite au moins 2 caractères.",
    response_model=Response,
)
@limiter.limit("60/minute")
async def quick_search(request: Request, q: str, db: AsyncSession = Depends(get_db)):
    if len(q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    cache_key = f"mathgraph:search:quick:{q.lower()}"
    try:
        cached = await redis_db.get(cache_key)
        if cached:
            return {"success": True, "data": json.loads(cached), "error": None, "meta": {"source": "cache"}}
    except Exception:
        pass

    results = await SearchService(db).global_quick_search(q)

    try:
        json_results = jsonable_encoder(results)
        await redis_db.set(cache_key, json.dumps(json_results), ex=3600)
    except Exception:
        pass

    return {"success": True, "data": results, "error": None, "meta": {"source": "db"}}


@router.post(
    "/advanced",
    status_code=201,
    summary="Recherche avancée",
    description="Effectue une recherche textuelle avancée en appliquant des filtres spécifiques de catégories. Nécessite au moins 2 caractères.",
    response_model=Response,
)
@limiter.limit("60/minute")
async def advanced_search(request: Request, payload: AdvancedSearchPayload, db: AsyncSession = Depends(get_db)):
    if len(payload.q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    cache_key = f"mathgraph:search:advanced:{payload.model_dump_json()}"
    try:
        cached = await redis_db.get(cache_key)
        if cached:
            return {"success": True, "data": json.loads(cached), "error": None, "meta": {"source": "cache"}}
    except Exception:
        pass

    results = await SearchService(db).advanced_search(payload.q, payload.filters)

    try:
        json_results = jsonable_encoder(results)
        await redis_db.set(cache_key, json.dumps(json_results), ex=3600)
    except Exception:
        pass

    return {"success": True, "data": results, "error": None, "meta": {"source": "db"}}
