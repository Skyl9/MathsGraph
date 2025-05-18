from typing import Dict

from fastapi import APIRouter

from app.schemas import UserResponse
from app.schemas.user import UserId, UpdateUser
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