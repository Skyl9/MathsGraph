from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import CreateData
from app.schemas.categorie import CategorieBase
from app.services import CategoryService

router = APIRouter(prefix="/category", tags=["category"])


@router.get("/{id_category}", response_model=CategorieBase)
async def get_one_category_E(id_category: int,db: AsyncConnection = Depends(get_db)):
    return await CategoryService(db).get_one_category(id_category)


@router.patch("/update/{id_category}")
async def update_category_E(id_category: int, data: dict,db: AsyncConnection = Depends(get_db)):
    await CategoryService(db).update_category(id_category, data)
    return {"message": "success"}


@router.get("/", response_model=list[CategorieBase])
async def all_category(db: AsyncConnection = Depends(get_db)):
    return await CategoryService(db).get_all_categories()


@router.post("/create")
async def create_category(data: CreateData,db: AsyncConnection = Depends(get_db)):
    return await CategoryService(db).add_category(data)


@router.get("/name/{name}", response_model=CategorieBase)
async def get_category_by_name(name: str,db: AsyncConnection = Depends(get_db)):
    return await CategoryService(db).get_category_id(name)
