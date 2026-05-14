from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_admin_payload
from app.core.exceptions import InternalServerError
from app.core.redis_client import redis_db
from app.db.database import get_db
from app.schemas import Response
from app.schemas.admin import Stat, ConceptForAdmin
from app.schemas.auth import User
from app.services.admin_service import AdminService, logger
from app.services.layout_service import LayoutService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=Response[Stat])
async def get_stats(db: AsyncConnection = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    try:
        data: Stat = await AdminService(db).get_stats()
        print(data)
        logger.debug(f"Route GET {router.prefix}/stats a renvoyé : ,{str(data)}")
        return {"error": None, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur de Route GET /{router.prefix}/stats : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/users", response_model=Response[List[User]])
async def get_users(db: AsyncConnection = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    try:
        data: List[User] = await AdminService(db).get_users()
        logger.debug(f"Route GET /{router.prefix}/users a renvoyé : {str(data)}")
        return {"error": None, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur de Route GET /{router.prefix}/users : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/contents", response_model=Response[List[ConceptForAdmin]])
async def get_contents(db: AsyncConnection = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    try:
        data: List[ConceptForAdmin] = await AdminService(db).get_concepts_admin()
        logger.debug(f"Route GET /{router.prefix}/contents a renvoyé : {str(data)} ")
        return {"error": None, "data": data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /{router.prefix}/contents a : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.post("/recalculate-graph", summary="Recalcule la physique 3D du graphe", response_model=Response)
async def recalculate_graph_layout(
        db: AsyncConnection = Depends(get_db),
        _payload: dict = Depends(get_current_admin_payload)
):
    try:
        # On lance le calcul physique
        await LayoutService(db).recalculate_positions()
        logger.debug(f"Route POST /{router.prefix}/recalculate-graph exécutée avec succès")
        await redis_db.delete("mathgraph:data")
        return {"error": None, "data": "Graphe recalculé avec succès", "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur de Route POST /{router.prefix}/recalculate-graph : {exc}")
        raise InternalServerError(str(exc)) from exc