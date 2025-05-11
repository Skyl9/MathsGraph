from typing import List

from fastapi import APIRouter

from app.schemas.concept import Mathematicien
from app.schemas.mathematicien import MathematicienResponse, MathematicienName

router = APIRouter(prefix="/mathematicien", tags=["mathematicien"])


@router.get("/{id_mathematicien}", response_model=MathematicienResponse)
async def get_one_mathematicien_E(id_mathematicien: int) -> MathematicienResponse:
    return Mathematicien.get_one_mathematicien(id_mathematicien)


@router.patch("/updateOneCategory/{id_mathematicien}")
async def updateOneCategoryMathematicien_E(id_mathematicien: int, data: dict):
    Mathematicien.update_mathematicien(id_mathematicien, data)
    return {"message": "success"}


@router.get("/", response_model=List[MathematicienName])
async def mathematicienName():
    return Mathematicien.get_all_mathematicien_name()
