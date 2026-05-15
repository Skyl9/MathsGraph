import json

import redis
from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.core.redis_client import redis_db
from app.db.database import get_db
from app.schemas import GraphData, Response
from app.services.graph_service import GraphService, logger

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=Response[GraphData])
async def get_graph(db: AsyncConnection = Depends(get_db)):
    cached_graph = None

    try:
        cached_graph = await redis_db.get("mathgraph:data")
    except redis.exceptions.ConnectionError:
        logger.warning("⚠️ Impossible de se connecter à Redis. Le cache est ignoré.")

    if cached_graph:
        logger.debug("Graphe servi depuis le cache Redis ⚡")
        return {"success": True, "data": json.loads(cached_graph), "error": None, "meta": {"source": "cache"}}

    try:
        graph: GraphData = await GraphService(db).get_graph()

        try:
            await redis_db.set("mathgraph:data", json.dumps(graph), ex=86400)
        except redis.exceptions.ConnectionError:
            pass

        logger.debug("Route GET /graph a renvoyé %d nœuds depuis PostgreSQL", len(graph["nodes"]))
        return {"success": True, "data": graph, "error": None, "meta": {"source": "db"}}

    except Exception as exc:
        logger.error("Erreur interne dans GET /graph (PostgreSQL) : %s", exc)
        raise InternalServerError(detail=str(exc))