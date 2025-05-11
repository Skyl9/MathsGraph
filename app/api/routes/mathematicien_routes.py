from typing import List

from fastapi import APIRouter

from app.schemas import CreateData
from app.schemas.mathematicien import MathematicienResponse, MathematicienName
from app.services import MathematicienService

router = APIRouter(prefix="/mathematicien", tags=["mathematicien"])


@router.get("/{id_mathematicien}", response_model=MathematicienResponse)
async def get_one_mathematicien_E(id_mathematicien: int) -> MathematicienResponse:
    return MathematicienService.get_one_mathematicien(id_mathematicien)


@router.patch("/update/{id_mathematicien}")
async def updateOneCategoryMathematicien_E(id_mathematicien: int, data: dict):
    MathematicienService.update_mathematicien(id_mathematicien, data)
    return {"message": "success"}


@router.get("/", response_model=List[MathematicienName])
async def mathematicienName():
    return MathematicienService.get_all_mathematicien_name()

@router.post('/create')
async def add_mathematicien(data:CreateData):
    MathematicienService.add_mathematicien(data)
