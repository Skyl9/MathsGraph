from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import GraphData, Response
from app.services.graph_service import GraphService, logger

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_model=Response[GraphData])
async def get_graph(db: AsyncConnection = Depends(get_db)):
    try:
        graph: GraphData = await GraphService(db).get_graph()
        logger.debug("Route GET /graph a renvoyé %d nœuds", len(graph["nodes"]))
        return {"success": True, "data": graph, "error": None, "meta": None}

    except InternalServerError as exc:
        logger.error("Erreur interne dans GET /graph : %s", exc)
        raise InternalServerError(detail=str(exc))
