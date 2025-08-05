from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateData
from app.schemas.type import TypeResponse
from app.services.type_service import TypeService

router = APIRouter(prefix="/type",tags=["type"])

@router.get("/{id_type}",response_model=TypeResponse)
async def get_one_type_E(id_type:int,db:AsyncConnection=Depends(get_db)):
    return await TypeService(db).get_one_type(id_type)

@router.patch("/update/{id_type}")
async def update_type_E(id_type:int,data:dict,db:AsyncConnection=Depends(get_db)):
    await TypeService(db).update_type(id_type,data,)
    return {"message":"success"}

@router.get("/",response_model=list[TypeResponse])
async def get_all_type(db:AsyncConnection=Depends(get_db)):
    return await TypeService(db).get_all_type_name()

@router.post("/create")
async def create_type(data : CreateData,db:AsyncConnection=Depends(get_db)):
    return await TypeService(db).add_type(data)
@router.get("/name/{name}",response_model=TypeResponse)
async def get_type_by_name(name:str,db:AsyncConnection=Depends(get_db)):
    return await TypeService(db).get_category_id(name)