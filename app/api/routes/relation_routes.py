from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, CreateRelation
from app.services.relation_service import RelationService, logger

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post("", summary="Crée une nouvelle relation", response_model=Response)
async def create_relation(
    data: CreateRelation, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    async with db.transaction():
        await RelationService(db).add_relation(data)
    logger.debug(f"Route POST /relation/create a correctement créé une relation")
    return {"error": None, "data": None, "success": True, "meta": None}
