from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, CreateData
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom
from app.services.type_service import TypeService, logger

router = APIRouter(prefix="/type", tags=["type"])


@router.get("/{id_type}", summary="Récupère un type par son ID", response_model=Response[TypeResponse])
async def get_one_type_E(id_type: int, db: AsyncSession = Depends(get_db)):
    type_data: TypeResponse = await TypeService(db).get_one_type(id_type)
    logger.debug(f"Route GET /{router.prefix}/{id_type} a renvoyé correctement : {type_data}")
    return {"error": None, "data": type_data, "success": True, "meta": None}


@router.patch("/{id_type}", summary="Met à jour un type", response_model=Response)
async def update_type_E(
    id_type: int,
    data: TypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await TypeService(db).update_type(id_type, data)
    await db.commit()
    logger.debug(f"Route PATCH /{router.prefix}/update/{id_type} a correctement mis à jour le type d'id : {id_type}")
    return {"error": None, "data": None, "success": True, "meta": None}


@router.get("/", summary="Récupère tous les types", response_model=Response[List[TypeNom]])
async def get_all_type(db: AsyncSession = Depends(get_db)):
    all_types: List[TypeNom] = await TypeService(db).get_all_type_name()  # type: ignore
    logger.debug(f"Route GET /{router.prefix}/ a renvoyé correctement : {all_types}")
    return {"error": None, "data": all_types, "success": True, "meta": None}


@router.post("", summary="Crée un nouveau type", response_model=Response)
async def create_type(
    data: CreateData, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    result = await TypeService(db).add_type(data)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/create a correctement créé un type")
    return {"error": None, "data": result, "success": True, "meta": None}


@router.get("/name/{name}", summary="Récupère un type par son nom", response_model=Response[TypeResponse])
async def get_type_by_name(name: str, db: AsyncSession = Depends(get_db)):
    type_data: TypeResponse = await TypeService(db).get_type_by_name(name)
    logger.debug(f"Route GET /{router.prefix}/name/{name} a renvoyé correctement : {type_data}")
    return {"error": None, "data": type_data, "success": True, "meta": None}
