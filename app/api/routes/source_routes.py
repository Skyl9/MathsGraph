from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response, CreateSource
from app.services.source_service import SourceService, logger

router = APIRouter(prefix="/source", tags=["source"])


@router.post("/create", summary="Crée une nouvelle source", response_model=Response)
async def create_source(data: CreateSource, db: AsyncConnection = Depends(get_db)):
    try:
        async with db.transaction():
            await SourceService(db).create_source(data)
        logger.debug(f"Route POST /source/create a correctement créé une source")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /source/create Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc