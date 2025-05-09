from fastapi import APIRouter

from app.schemas.mathematicien import MathematicienResponse, MathematicienUpdate
from app.services.mathematicien_service import get_one_mathematicien, update_mathematicien

router = APIRouter(prefix="/mathematicien", tags=["mathematicien"])

@router.get("/{id_mathematicien}",response_model=MathematicienResponse)
async def get_one_mathematicien_E(id_mathematicien:int)->MathematicienResponse:
    return get_one_mathematicien(id_mathematicien)

@router.patch("/updateOneCategory/{id_mathematicien}")
async def updateOneCategoryMathematicien_E(id_mathematicien:int,data:dict):
    print(data)
    update_mathematicien(id_mathematicien,data)
    return {"message":"success"}