from pydantic import BaseModel
from typing import Optional
from .base import TimestampModel

class AliasBase(BaseModel):
    alias: str
    description: Optional[str] = None

class AliasCreate(AliasBase):
    concept_id: int

class AliasResponse(AliasBase, TimestampModel):
    id: int