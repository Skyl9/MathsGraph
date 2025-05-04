from pydantic import BaseModel, EmailStr
from typing import Optional
from .base import TimestampModel

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase, TimestampModel):
    id: int

class UserInDB(UserResponse):
    hashed_password: str