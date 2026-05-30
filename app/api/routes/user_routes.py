from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.core.exceptions import ForbiddenException
from app.db.database import get_db
from app.schemas import Response, UserResponse
from app.schemas.user import UserId, UpdateUser, Favorite, FavoriteResponse
from app.services.user_service import UserService, logger

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/{id_user}", summary="Récupère un utilisateur par son ID", response_model=Response[UserResponse])
async def get_user_by_id(id_user: int, db: AsyncSession = Depends(get_db)):
    user_data: UserResponse = await UserService(db).get_user_by_id(id_user)
    logger.debug(f'Route GET /{router.prefix}/{id_user} a renvoyé correctement : {user_data}')
    return {"error": None, "data": user_data, "success": True, "meta": None}


@router.get("/id/{username}", summary="Récupère l'ID d'un utilisateur par son nom", response_model=Response[UserId])
async def get_id_by_username(username: str, db: AsyncSession = Depends(get_db)):
    user_id: UserId = await UserService(db).get_id_by_username(username)
    logger.debug(f'Route GET /{router.prefix}/id/{username} a renvoyé correctement : {user_id}')
    return {"error": None, "data": user_id, "success": True, "meta": None}


@router.patch("/{id_user}", summary="Met à jour les informations d'un utilisateur", response_model=Response)
async def patch_user(
    id_user: int, 
    data: UpdateUser, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    await UserService(db).patch_user(id_user, data, current_user)
    await db.commit()
    logger.debug(f"Route PATCH /{router.prefix}/update/{id_user} a correctement mis à jour l'utilisateur d'id : {id_user}")
    return {"error": None, "data": None, "success": True, "meta": None}

@router.get("/history/{id_user}", summary="Donne la liste des concepts modifié par un utilisateur")
async def get_history_user(id_user: int,
                           limit: int = Query(20, ge=1, le=100),
                           db: AsyncSession = Depends(get_db)):
    data = await UserService(db).get_history_user(id_user, limit)
    return {"error": None, "data": data, "success": True, "meta": None}

@router.get("/favorite/{user_id}", summary="Récupère les favoris d'un utilisateur", response_model=Response[List[FavoriteResponse]])
async def get_favorite_user(user_id: int, db: AsyncSession = Depends(get_db)):
    favorites = await UserService(db).get_favorite_user(user_id)
    logger.debug(f'Route GET /{router.prefix}/favorite/{user_id} a renvoyé correctement : {favorites}')
    return {"error": None, "data": favorites, "success": True, "meta": None}


@router.delete("/favorite/{general_id}", summary="Supprime un favori d'un utilisateur", response_model=Response)
async def delete_favorite_user(
    general_id: int, 
    data: Favorite, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    caller_id = current_user.get("id")
    caller_role = current_user.get("role", "").lower()
    if int(data.user_id) != caller_id and caller_role != "admin":
        raise ForbiddenException(detail="Not authorized to modify this user's favorites")

    await UserService(db).delete_favorite_user(general_id, data)
    await db.commit()
    return {"error": None, "data": None, "success": True, "meta": None}


@router.post("/favorite/{general_id}", summary="Ajoute un favori à un utilisateur", response_model=Response)
async def add_favorite_user(
    general_id: int, 
    data: Favorite, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    caller_id = current_user.get("id")
    caller_role = current_user.get("role", "").lower()
    if int(data.user_id) != caller_id and caller_role != "admin":
        raise ForbiddenException(detail="Not authorized to modify this user's favorites")

    await UserService(db).add_favorite_user(general_id, data)
    await db.commit()
    logger.debug(f"Route POST /{router.prefix}/favorite/add/{general_id} a correctement ajouté le favori")
    return {"error": None, "data": None, "success": True, "meta": None}