from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateData
from app.schemas.mathematicien import MathematicienResponse, MathematicienName
from app.services import MathematicienService

router = APIRouter(prefix="/mathematicien", tags=["mathematicien"])


@router.get("/{id_mathematicien}", response_model=MathematicienResponse)
async def get_one_mathematicien_E(id_mathematicien: int,db:AsyncConnection=Depends(get_db)) -> MathematicienResponse:
    return await MathematicienService(db).get_one_mathematicien(id_mathematicien)


@router.patch("/update/{id_mathematicien}")
async def updateOneCategoryMathematicien_E(id_mathematicien: int, data: dict,db:AsyncConnection=Depends(get_db)):
    await MathematicienService(db).update_mathematicien(id_mathematicien, data)
    return {"message": "success"}


@router.get("/", response_model=List[MathematicienName])
async def mathematicienName(db:AsyncConnection=Depends(get_db)):
    return await MathematicienService(db).get_all_mathematicien_name()

@router.post('/create')
async def add_mathematicien(data:CreateData,db:AsyncConnection=Depends(get_db)):
    await MathematicienService(db).add_mathematicien(data)
@router.get("/name/{name}", response_model=MathematicienResponse)
async def get_mathematicien_by_name(name:str,db:AsyncConnection=Depends(get_db)):
    return await MathematicienService(db).get_mathematicien_id(name)