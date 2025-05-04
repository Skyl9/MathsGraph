from pydantic import BaseModel
from typing import Optional
from .base import TimestampModel

class NomEtrangerBase(BaseModel):
    nom: str
    langue: str
    pays: Optional[str] = None
    notes: Optional[str] = None

class NomEtrangerCreate(NomEtrangerBase):
    concept_id: int

class NomEtrangerResponse(NomEtrangerBase, TimestampModel):
    id: int