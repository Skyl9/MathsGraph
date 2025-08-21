from pydantic import BaseModel, EmailStr
from typing import Optional
from .base import TimestampModel

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True
    role: Optional[str] = None


class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase,TimestampModel):
    id: int
    created_at: str
    preferred_language: Optional[str] = None
    avatar_url :Optional[str] = None
    bio:Optional[str] = None


class UserInDB(UserResponse):
    hashed_password: str

class UserId(BaseModel):
    id: int
class UpdateUser(BaseModel):
    field:str
    value:str

class Favorite(BaseModel):
    type:str
    user_id:str

class FavoriteResponse(BaseModel):
    id:int
    nom:str
    category:str