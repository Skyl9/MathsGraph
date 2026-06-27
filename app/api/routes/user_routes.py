from app.core.limiter import limiter
from typing import List
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response, UserResponse
from app.schemas.user import UserId, UpdateUser, Favorite, FavoriteResponse
from app.services.user_service import UserService, logger

router = APIRouter(prefix="/users", tags=["user"])


@router.get(
    "/{id_user}",
    summary="Récupère un utilisateur par son ID",
    description="Retourne les informations détaillées d'un utilisateur en fonction de son identifiant unique.",
    response_model=Response[UserResponse],
)
async def get_user_by_id(id_user: PyUUID, db: AsyncSession = Depends(get_db)):
    user_data: UserResponse = await UserService(db).get_user_by_id(id_user)
    logger.debug(f"Route GET /{router.prefix}/{id_user} a renvoyé correctement : {user_data}")
    return {"error": None, "data": user_data, "success": True, "meta": None}


@router.get(
    "/id/{username}",
    summary="Récupère l'ID d'un utilisateur par son nom",
    description="Permet de retrouver l'identifiant d'un utilisateur à partir de son nom d'utilisateur exact.",
    response_model=Response[UserId],
)
async def get_id_by_username(username: str, db: AsyncSession = Depends(get_db)):
    user_id: UserId = await UserService(db).get_id_by_username(username)
    logger.debug(f"Route GET /{router.prefix}/id/{username} a renvoyé correctement : {user_id}")
    return {"error": None, "data": user_id, "success": True, "meta": None}


@router.patch(
    "/{id_user}",
    summary="Met à jour les informations d'un utilisateur",
    description="Modifie les données d'un utilisateur existant (nécessite d'être authentifié et d'avoir les droits nécessaires).",
    response_model=Response,
)
async def patch_user(
    id_user: PyUUID,
    data: UpdateUser,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await UserService(db).patch_user(id_user, data, current_user)
    logger.debug(
        f"Route PATCH /{router.prefix}/update/{id_user} a correctement mis à jour l'utilisateur d'id : {id_user}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.get(
    "/history/{id_user}",
    summary="Donne la liste des concepts modifiés par un utilisateur",
    description="Récupère l'historique des modifications apportées aux concepts par un utilisateur spécifique avec pagination.",
    response_model=Response,
)
async def get_history_user(id_user: PyUUID, limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    data = await UserService(db).get_history_user(id_user, limit)
    return {"error": None, "data": data, "success": True, "meta": None}


@router.get(
    "/favorite/{user_id}",
    summary="Récupère les favoris d'un utilisateur",
    description="Renvoie la liste des concepts marqués comme favoris par l'utilisateur.",
    response_model=Response[List[FavoriteResponse]],
)
async def get_favorite_user(user_id: PyUUID, db: AsyncSession = Depends(get_db)):
    favorites = await UserService(db).get_favorite_user(user_id)
    logger.debug(f"Route GET /{router.prefix}/favorite/{user_id} a renvoyé correctement : {favorites}")
    return {"error": None, "data": favorites, "success": True, "meta": None}


@router.delete(
    "/favorite/{general_id}",
    status_code=204,
    summary="Supprime un favori d'un utilisateur",
    description="Retire un concept de la liste des favoris de l'utilisateur connecté.",
)
async def delete_favorite_user(
    general_id: int,
    data: Favorite,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await UserService(db).delete_favorite_user(general_id, data, current_user)
    return None


@router.post(
    "/favorite/{general_id}",
    status_code=201,
    summary="Ajoute un favori à un utilisateur",
    description="Ajoute un concept à la liste des favoris de l'utilisateur connecté.",
    response_model=Response,
)
@limiter.limit("20/minute")
async def add_favorite_user(
    request: Request,
    general_id: int,
    data: Favorite,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await UserService(db).add_favorite_user(general_id, data, current_user)
    logger.debug(f"Route POST /{router.prefix}/favorite/add/{general_id} a correctement ajouté le favori")
    return {"error": None, "data": None, "success": True, "meta": None}
