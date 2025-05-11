from fastapi import APIRouter

from app.db.database import get_db_connection
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/concepts/{concept_id}")
def get_concept_views(concept_id: int):
    return StatisticsService.get_concept_views(concept_id)