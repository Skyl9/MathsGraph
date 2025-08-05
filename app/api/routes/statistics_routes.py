from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db_connection, get_db
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/concepts/{concept_id}")
async def get_concept_views(concept_id: int,db:AsyncConnection=Depends(get_db)):
    return await StatisticsService(db).get_concept_views(concept_id)