import json
import redis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import redis_db
from app.db.database import get_db
from app.schemas import GraphData, Response
from app.services.graph_service import GraphService, logger

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=Response[GraphData])
async def get_graph(db: AsyncSession = Depends(get_db)):
    cached_graph = None

    try:
        cached_graph = await redis_db.get("mathgraph:data")
    except redis.exceptions.ConnectionError:
        logger.warning("⚠️ Impossible de se connecter à Redis. Le cache est ignoré.")

    if cached_graph:
        logger.debug("Graphe servi depuis le cache Redis ⚡")
        return {"success": True, "data": json.loads(cached_graph), "error": None, "meta": {"source": "cache"}}

    graph: GraphData = await GraphService(db).get_graph()

    try:
        await redis_db.set("mathgraph:data", graph.model_dump_json(), ex=86400)
    except redis.exceptions.ConnectionError:
        pass

    logger.debug("Route GET /graph a renvoyé %d nœuds depuis PostgreSQL", len(graph.nodes) if graph.nodes else 0)
    return {"success": True, "data": graph, "error": None, "meta": {"source": "db"}}
