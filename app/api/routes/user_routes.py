from typing import Dict

from fastapi import APIRouter, Body

from app.schemas import UserResponse
from app.schemas.user import UserId, UpdateUser, Favorite
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/{id_user}",response_model=UserResponse)
async def get_user_by_id(id_user: int):
    return UserService.get_user_by_id(id_user)

@router.get("/id/{username}",response_model=UserId)
async def get_id_by_username(username:str):
    return UserService.get_id_by_username(username)

@router.patch("/update/{id_user}")
async def patch_user(id_user:str, data:UpdateUser):
    return UserService.patch_user(id_user,data)

@router.get("/favorite/{user_id}")
async def get_favorite_user(user_id:int):
    return UserService.get_favorite_user(user_id)

@router.delete("/favorite/delete/{general_id}")
async def delete_favorite_user(general_id:int,data:Favorite):
    return UserService.delete_favorite_user(general_id,data)

@router.post("/favorite/add/{general_id}")
async def add_favorite_user(general_id:int,data:Favorite):
    return UserService.add_favorite_user(general_id,data)