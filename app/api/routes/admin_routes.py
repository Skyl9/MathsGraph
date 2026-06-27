from app.core.limiter import limiter
from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_payload
from app.core.redis_client import redis_db
from app.db.database import get_db
from app.schemas import Response
from app.schemas.admin import Stat, ConceptForAdmin, RecentActivityItem
from app.schemas.auth import User
from app.services.admin_service import AdminService, logger
from app.services.layout_service import LayoutService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/stats",
    summary="Obtenir les statistiques",
    description="Renvoie les statistiques globales de l'application (nombre d'utilisateurs, de concepts, etc.). L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response[Stat],
)
async def get_stats(db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data: Stat = await AdminService(db).get_stats()
    logger.debug(f"Route GET {router.prefix}/stats a été appelée avec succès")
    return {"error": None, "data": data, "success": True, "meta": None}


@router.get(
    "/users",
    summary="Lister les utilisateurs",
    description="Récupère la liste de tous les utilisateurs enregistrés avec pagination. L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response[List[User]],
)
async def get_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _payload: dict = Depends(get_current_admin_payload),
):
    result = await AdminService(db).get_users(skip=skip, limit=limit)
    logger.debug(
        f"Route GET /{router.prefix}/users a été appelée avec succès, {len(result['items'])} utilisateurs trouvés"
    )
    return {
        "error": None,
        "data": result["items"],
        "success": True,
        "meta": {"total": result["total"], "skip": skip, "limit": limit},
    }


@router.get(
    "/contents",
    summary="Lister les concepts (Admin)",
    description="Récupère la liste des concepts pour l'interface d'administration avec pagination. L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response[List[ConceptForAdmin]],
)
async def get_contents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _payload: dict = Depends(get_current_admin_payload),
):
    result = await AdminService(db).get_concepts_admin(skip=skip, limit=limit)
    logger.debug(
        f"Route GET /{router.prefix}/contents a été appelée avec succès, {len(result['items'])} concepts trouvés"
    )
    return {
        "error": None,
        "data": result["items"],
        "success": True,
        "meta": {"total": result["total"], "skip": skip, "limit": limit},
    }


@router.post(
    "/recalculate-graph",
    status_code=201,
    summary="Recalcule la physique 3D du graphe",
    description="Déclenche le recalcul des positions physiques 3D de tous les noeuds du graphe et purge le cache Redis. L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response,
)
@limiter.limit("20/minute")
async def recalculate_graph_layout(
    request: Request, db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)
):
    await LayoutService(db).recalculate_positions()
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/recalculate-graph exécutée avec succès")
    await redis_db.delete("mathgraph:data")
    return {"error": None, "data": "Graphe recalculé avec succès", "success": True, "meta": None}


@router.get(
    "/analytics",
    summary="Données d'utilisation de l'API",
    description="Récupère les données d'analyse d'utilisation de l'API (requêtes, erreurs, latence). L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response,
)
async def get_analytics(db: AsyncSession = Depends(get_db), _payload: dict = Depends(get_current_admin_payload)):
    data = await AdminService(db).get_api_analytics()
    logger.debug(f"Route GET /{router.prefix}/analytics exécutée avec succès")
    return {"error": None, "data": data, "success": True, "meta": None}


@router.get(
    "/recent-activity",
    summary="Obtenir l'activité récente",
    description="Renvoie la liste des dernières modifications effectuées sur la base de données. L'utilisateur doit avoir le rôle administrateur.",
    response_model=Response[List[RecentActivityItem]],
)
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _payload: dict = Depends(get_current_admin_payload),
):
    data = await AdminService(db).get_recent_activity(limit=limit)
    logger.debug(
        f"Route GET /{router.prefix}/recent-activity a été appelée avec succès, {len(data)} activités trouvées"
    )
    return {"error": None, "data": data, "success": True, "meta": None}
