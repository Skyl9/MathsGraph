from typing import Dict

from fastapi import APIRouter, Body, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas import UserResponse
from app.schemas.user import UserId, UpdateUser, Favorite
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/{id_user}",response_model=UserResponse)
async def get_user_by_id(id_user: int,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).get_user_by_id(id_user)

@router.get("/id/{username}",response_model=UserId)
async def get_id_by_username(username:str,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).get_id_by_username(username)

@router.patch("/update/{id_user}")
async def patch_user(id_user:str, data:UpdateUser,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).patch_user(id_user,data)

@router.get("/favorite/{user_id}")
async def get_favorite_user(user_id:int,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).get_favorite_user(user_id)

@router.delete("/favorite/delete/{general_id}")
async def delete_favorite_user(general_id:int,data:Favorite,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).delete_favorite_user(general_id,data)

@router.post("/favorite/add/{general_id}")
async def add_favorite_user(general_id:int,data:Favorite,db:AsyncConnection=Depends(get_db)):
    return await UserService(db).add_favorite_user(general_id,data)