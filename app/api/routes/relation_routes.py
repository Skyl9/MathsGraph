from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateRelation
from app.services.relation_service import RelationService

router = APIRouter(prefix="/relation", tags=["relation"])

@router.post("/create")
async def create_relation(data: CreateRelation,db:AsyncConnection=Depends(get_db)):
    return await RelationService(db).add_relation(data)
