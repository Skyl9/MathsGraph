from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import CreateData, Response
from app.schemas.categorie import CategorieBase, CategoryUpdate
from app.services import CategoryService
from app.services.category_service import logger

router = APIRouter(prefix="/category", tags=["category"])


@router.get(
    "/{id_category}",
    summary="Récupère une catégorie par son ID",
    description="Retourne les détails d'une catégorie spécifique en fonction de son identifiant unique.",
    response_model=Response[CategorieBase],
)
async def get_one_category_E(id_category: int, db: AsyncSession = Depends(get_db)):
    category: CategorieBase = await CategoryService(db).get_one_category(id_category)
    logger.debug(f"Route GET /{router.prefix}/{id_category} a renvoyé correctement la catégorie : , {str(category)}")
    return {"error": None, "success": True, "data": category, "meta": None}


@router.patch(
    "/{id_category}",
    summary="Met à jour une catégorie",
    description="Modifie les informations d'une catégorie existante via son identifiant. Nécessite des droits d'administration ou un accès valide.",
    response_model=Response,
)
async def update_category_E(
    id_category: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await CategoryService(db).update_category(id_category, data, current_user)
    await db.commit()
    logger.debug(f"Route PATCH /{router.prefix}/update/{id_category} a modifié correctement la catégorie {id_category}")
    return {"error": None, "success": True, "data": None, "meta": None}


@router.get(
    "/",
    summary="Récupère la liste de toutes les catégories",
    description="Retourne la liste complète de toutes les catégories enregistrées dans le système.",
    response_model=Response[list[CategorieBase]],
)
async def all_category(db: AsyncSession = Depends(get_db)):
    list_cat: list[CategorieBase] = await CategoryService(db).get_all_categories()
    logger.debug(f"Route GET /{router.prefix}/ a renvoyé correctement la liste des catégories : , {str(list_cat)}")
    return {"error": None, "success": True, "data": list_cat, "meta": None}


@router.post(
    "",
    summary="Crée une nouvelle catégorie",
    description="Ajoute une nouvelle catégorie dans la base de données. L'utilisateur authentifié est pris en compte pour la création.",
    response_model=Response,
)
async def create_category(
    data: CreateData, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await CategoryService(db).add_category(data, current_user)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/create a créer correctement la catégorie : ,{str(data)}")
    return {"error": None, "success": True, "data": None, "meta": None}


@router.get(
    "/name/{name}",
    summary="Récupère une catégorie par son nom",
    description="Recherche et retourne les informations d'une catégorie en se basant sur son nom exact.",
    response_model=Response[CategorieBase],
)
async def get_category_by_name(name: str, db: AsyncSession = Depends(get_db)):
    cat: CategorieBase = await CategoryService(db).get_category_id_by_name(name)
    logger.debug(f"Route GET /{router.prefix}/name/{name} a renvoyé correctement la catégorie : , {str(cat)}")
    return {"error": None, "success": True, "data": cat, "meta": None}
