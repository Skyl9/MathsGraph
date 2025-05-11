from fastapi import APIRouter

from app.schemas import CreateAlias
from app.services.alias_service import AliasService

router = APIRouter(prefix="/alias", tags=["alias"])


@router.post("/create")
async def create_alias(data: CreateAlias):
    return AliasService.add_alias(data)
