from fastapi import APIRouter

from app.schemas import CreateRelation
from app.services.relation_service import RelationService

router = APIRouter(prefix="/relation", tags=["relation"])

@router.post("/create")
async def create_relation(data: CreateRelation):
    return RelationService.add_relation(data)
