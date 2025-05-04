from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ConceptHistory(BaseModel):
    concept_id: int
    modified_by: int
    old_value: dict
    new_value: dict
    field_modified: str

class Comment(BaseModel):
    concept_id: int
    user_id: int
    content: str
    parent_id: Optional[int] = None

class ConceptValidation(BaseModel):
    concept_id: int
    validator_id: int
    status: str
    comments: Optional[str] = None
