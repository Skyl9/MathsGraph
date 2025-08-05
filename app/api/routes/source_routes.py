from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateSource
from app.services.source_service import SourceService

router = APIRouter(prefix="/source",tags=["source"])

@router.post("/create",response_model=dict)
async def create_source(data:CreateSource,db:AsyncConnection=Depends(get_db)):
    await SourceService(db).create_source(data)
    return {"message":"success"}