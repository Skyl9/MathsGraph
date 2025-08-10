from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: Optional[str]
    created_at: Optional[datetime]

class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

class PasswordResetConfirmSchema(BaseModel):
    new_password: str
    token: str