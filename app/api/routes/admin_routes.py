from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response
from app.schemas.admin import Stat, ConceptForAdmin
from app.schemas.auth import User
from app.services.admin_service import AdminService, logger

router = APIRouter(prefix="/admin", tags=["alias"])


@router.get("/stats", response_model=Response[Stat])
async def get_stats(db: AsyncConnection = Depends(get_db)):
    try:
        data: Stat = await AdminService(db).get_stats()
        logger.debug(f"Route GET /{router.prefix}/stats a renvoyé : ",str(data))
        return {"error": False, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur de Route GET /{router.prefix}/stats : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/users", response_model=Response[List[User]])
async def get_users(db: AsyncConnection = Depends(get_db)):
    try:
        data: List[User] = await AdminService(db).get_users()
        logger.debug(f"Route GET /{router.prefix}/users a renvoyé : {str(data)}")
        return {"error": False, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur de Route GET /{router.prefix}/users : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/contents", response_model=Response[List[ConceptForAdmin]])
async def get_contents(db: AsyncConnection = Depends(get_db)):
    try:
        data: List[ConceptForAdmin] = await AdminService(db).get_concepts_admin()
        logger.debug(f"Route GET /{router.prefix}/contents a renvoyé : {str(data)} ")
        return {"error": False, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /{router.prefix}/contents a : {str(exc)}")
        raise InternalServerError(str(exc)) from exc
