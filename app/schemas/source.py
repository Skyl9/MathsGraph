from pydantic import BaseModel
from typing import Optional
from .base import TimestampModel


class SourceBase(BaseModel):
    titre: str
    auteur: Optional[str] = None
    annee: Optional[int] = None
    url: Optional[str] = None
    type: Optional[str] = None  # livre, article, web, etc.
    details: Optional[str] = None


class SourceCreate(SourceBase):
    id: int


class SourceResponse(SourceBase, TimestampModel):
    id: int
