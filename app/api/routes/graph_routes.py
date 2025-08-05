from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import GraphData
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/",response_model=GraphData)
async def get_graph(db:AsyncConnection=Depends(get_db)):
    return GraphService(db).get_graph()