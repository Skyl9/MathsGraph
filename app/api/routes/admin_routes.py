import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_payload
from app.core.redis_client import redis_db
from app.db.database import get_db
from app.schemas import Response
from app.schemas.admin import Stat, ConceptForAdmin
from app.schemas.auth import User
from app.services.admin_service import AdminService, logger
from app.services.layout_service import LayoutService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=Response[Stat])
async def get_stats(db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data: Stat = await AdminService(db).get_stats()
    logger.debug(f"Route GET {router.prefix}/stats a renvoyé : ,{str(data)}")
    return {"error": None, "data": data, "success": True, "meta": None}


@router.get("/users", response_model=Response[List[User]])
async def get_users(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data: List[User] = await AdminService(db).get_users(skip=skip, limit=limit)
    logger.debug(f"Route GET /{router.prefix}/users a renvoyé : {str(data)}")
    return {"error": None, "data": data, "success": True, "meta": None}


@router.get("/contents", response_model=Response[List[ConceptForAdmin]])
async def get_contents(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data: List[ConceptForAdmin] = await AdminService(db).get_concepts_admin(skip=skip, limit=limit)
    logger.debug(f"Route GET /{router.prefix}/contents a renvoyé : {str(data)} ")
    return {"error": None, "data": data, "success": True, "meta": None}


@router.post("/recalculate-graph", summary="Recalcule la physique 3D du graphe", response_model=Response)
async def recalculate_graph_layout(
        db: AsyncSession = Depends(get_db),
        _payload: dict = Depends(get_current_admin_payload)
):
    await LayoutService(db).recalculate_positions()
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/recalculate-graph exécutée avec succès")
    await redis_db.delete("mathgraph:data")
    return {"error": None, "data": "Graphe recalculé avec succès", "success": True, "meta": None}


@router.get("/analytics", summary="Données d'utilisation de l'API")
async def get_analytics(db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data = await AdminService(db).get_api_analytics()
    logger.debug(f"Route GET /{router.prefix}/analytics exécutée avec succès")
    return {"error": None, "data": data, "success": True, "meta": None}
