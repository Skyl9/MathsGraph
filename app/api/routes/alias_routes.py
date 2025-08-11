from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import CreateAlias, Response
from app.services.alias_service import AliasService, logger

router = APIRouter(prefix="/alias", tags=["alias"])


@router.post("/create", response_model=Response)
async def create_alias(data: CreateAlias, db: AsyncConnection = Depends(get_db)):
    try:
        await AliasService(db).add_alias(data)
        logger.debug(f"Route POST /{router.prefix}/alias : {data} ")
        return {"success": True, "data": None, "meta": None, "error": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/alias : {exc}")
        raise InternalServerError(detail=str(exc))
