from fastapi import APIRouter

from app.schemas.type import TypeResponse
from app.services.type_service import get_one_type, update_type, get_all_type_name

router = APIRouter(prefix="/type",tags=["type"])

@router.get("/{id_type}",response_model=TypeResponse)
async def get_one_type_E(id_type:int):
    return get_one_type(id_type)

@router.patch("/update/{id_type}")
async def update_type_E(id_type:int,data:dict):
    update_type(id_type,data)
    return {"message":"success"}

@router.get("/",response_model=list[TypeResponse])
async def get_all_type():
    return get_all_type_name()