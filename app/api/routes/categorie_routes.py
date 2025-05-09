from fastapi import APIRouter

from app.schemas.categorie import CategorieBase
from app.services.category_service import get_one_category, update_category, get_all_categories

router = APIRouter(prefix="/category", tags=["category"])

@router.get("/{id_category}",response_model=CategorieBase)
async def get_one_category_E(id_category:int):
    return get_one_category(id_category)

@router.patch("/update/{id_category}")
async def update_category_E(id_category:int,data:dict):
    update_category(id_category,data)
    return {"message":"success"}

@router.get("/",response_model=list[CategorieBase])
async def all_category():
    return get_all_categories()


