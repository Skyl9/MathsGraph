from fastapi import APIRouter, Depends
from psycopg import AsyncConnection
from pydantic import BaseModel

from app.db.database import get_db
from app.services.search_service import SearchService

class AdvancedSearchPayload(BaseModel):
    q: str
    filters: dict

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/quick", summary="Recherche globale rapide")
async def quick_search(q: str, db: AsyncConnection = Depends(get_db)):
    if len(q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    results = await SearchService(db).global_quick_search(q)
    return {"success": True, "data": results, "error": None, "meta": None}


@router.post("/advanced",summary="Recherche spécifique à une catégorie choisi")
async def advanced_search(payload :AdvancedSearchPayload, db: AsyncConnection = Depends(get_db)):
    if len(payload.q) < 2:
        return {"success": True, "data": [], "error": None, "meta": None}

    results = await SearchService(db).advanced_search(payload.q, payload.filters)
    return {"success": True, "data": results, "error": None, "meta": None}