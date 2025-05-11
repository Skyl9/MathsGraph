from fastapi import APIRouter

from app.schemas import CreateData
from app.schemas.categorie import CategorieBase
from app.services import CategoryService

router = APIRouter(prefix="/category", tags=["category"])


@router.get("/{id_category}", response_model=CategorieBase)
async def get_one_category_E(id_category: int):
    return CategoryService.get_one_category(id_category)


@router.patch("/update/{id_category}")
async def update_category_E(id_category: int, data: dict):
    CategoryService.update_category(id_category, data)
    return {"message": "success"}


@router.get("/", response_model=list[CategorieBase])
async def all_category():
    return CategoryService.get_all_categories()

@router.post("/create")
async def create_category(data:CreateData):
    return CategoryService.add_category(data)
