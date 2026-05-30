from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import CreateData, Response, UpdateConceptDict
from app.schemas.categorie import CategorieBase
from app.services import CategoryService
from app.services.category_service import logger

router = APIRouter(prefix="/category", tags=["category"])


@router.get("/{id_category}", response_model=Response[CategorieBase])
async def get_one_category_E(id_category: int, db: AsyncSession = Depends(get_db)):
    category: CategorieBase = await CategoryService(db).get_one_category(id_category)
    logger.debug(f"Route GET /{router.prefix}/{id_category} a renvoyé correctement la catégorie : , {str(category)}")
    return {"error": None, "success": True, "data": category, "meta": None}


@router.patch("/{id_category}", response_model=Response)
async def update_category_E(
    id_category: int, 
    data: UpdateConceptDict, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    await CategoryService(db).update_category(id_category, data)
    await db.commit()
    logger.debug(
        f"Route PATCH /{router.prefix}/update/{id_category} a modifié correctement la catégorie {id_category}")
    return {"error": None, "success": True, "data": None, "meta": None}


@router.get("/", response_model=Response[list[CategorieBase]])
async def all_category(db: AsyncSession = Depends(get_db)):
    list_cat: list[CategorieBase] = await CategoryService(db).get_all_categories()
    logger.debug(f"Route GET /{router.prefix}/ a renvoyé correctement la liste des catégories : , {str(list_cat)}")
    return {"error": None, "success": True, "data": list_cat, "meta": None}


@router.post("", response_model=Response)
async def create_category(
    data: CreateData, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    await CategoryService(db).add_category(data)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/create a créer correctement la catégorie : ,{str(data)}")
    return {"error": None, "success": True, "data": None, "meta": None}


@router.get("/name/{name}", response_model=Response[CategorieBase])
async def get_category_by_name(name: str, db: AsyncSession = Depends(get_db)):
    cat: CategorieBase = await CategoryService(db).get_category_id_by_name(name)
    logger.debug(f"Route GET /{router.prefix}/name/{name} a renvoyé correctement la catégorie : , {str(cat)}")
    return {"error": None, "success": True, "data": cat, "meta": None}
