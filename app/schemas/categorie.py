from pydantic import BaseModel
from typing import Optional

class CategorieBase(BaseModel):
    id:int
    nom: str
    description: Optional[str] = None

class CategoryUpdate(BaseModel):
    field:str
    value:dict