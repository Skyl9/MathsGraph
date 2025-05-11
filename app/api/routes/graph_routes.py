from fastapi import APIRouter

from app.schemas import GraphData
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/",response_model=GraphData)
async def get_graph():
    return GraphService.get_graph()