from fastapi import APIRouter

from app.schemas import CreateSource
from app.services.source_service import SourceService

router = APIRouter(prefix="/source",tags=["source"])

@router.post("/create",response_model=dict)
async def create_source(data:CreateSource):
    SourceService.create_source(data)
    return {"message":"success"}