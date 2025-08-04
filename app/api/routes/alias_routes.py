from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateAlias
from app.services.alias_service import AliasService

router = APIRouter(prefix="/alias", tags=["alias"])


@router.post("/create")
async def create_alias(data: CreateAlias,db:AsyncConnection = Depends(get_db)):
    return await AliasService(db).add_alias(data)
