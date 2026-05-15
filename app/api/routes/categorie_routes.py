from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import CreateData, Response
from app.schemas.categorie import CategorieBase
from app.services import CategoryService
from app.services.category_service import logger

router = APIRouter(prefix="/category", tags=["category"])


@router.get("/{id_category}", response_model=Response[CategorieBase])
async def get_one_category_E(id_category: int, db: AsyncConnection = Depends(get_db)):
    try:
        category: CategorieBase = await CategoryService(db).get_one_category(id_category)
        logger.debug(f"Route GET /{router.prefix}/{id_category} a renvoyé correctement la catégorie : , {str(category)}")
        return {"error": None, "success": True, "data": category, "meta": None}

    except InternalServerError as exc:
        logger.error(f"Route GET /{router.prefix}/{id_category} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.patch("/{id_category}", response_model=Response)
async def update_category_E(
    id_category: int, 
    data: dict, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await CategoryService(db).update_category(id_category, data)
        logger.debug(
            f"Route PATCH /{router.prefix}/update/{id_category} a modifié correctement la catégorie {id_category}")
        return {"error": None, "success": True, "data": None, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route PATCH /{router.prefix}/update/{id_category} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/", response_model=Response[list[CategorieBase]])
async def all_category(db: AsyncConnection = Depends(get_db)):
    try:
        listCat: list[CategorieBase] = await CategoryService(db).get_all_categories()
        logger.debug(f"Route GET /{router.prefix}/ a renvoyé correctement la liste des catégories : , {str(listCat)}")
        return {"error": None, "success": True, "data": listCat, "meta": None}

    except InternalServerError as exc:
        logger.error(f"Route GET /{router.prefix}/ Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.post("", response_model=Response)
async def create_category(
    data: CreateData, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await CategoryService(db).add_category(data)
        logger.debug(f"Route POST /{router.prefix}/create a créer correctement la catégorie : ,{str(data)}")
        return {"error": None, "success": True, "data": None, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/create Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/name/{name}", response_model=Response[CategorieBase])
async def get_category_by_name(name: str, db: AsyncConnection = Depends(get_db)):
    try:
        cat: CategorieBase = await CategoryService(db).get_category_id_by_name(name)
        logger.debug(f"Route GET /{router.prefix}/name/{name} a renvoyé correctement la catégorie : , {str(cat)}")
        return {"error": None, "success": True, "data": cat, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /{router.prefix}/name/{name} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc
