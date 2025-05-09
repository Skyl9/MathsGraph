from __future__ import annotations  # Activer les annotations différées (Python 3.7+)
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from relation import RelationResponse
    from source import SourceResponse


class ConceptBase(BaseModel):
    nom: str
    enonce: Optional[str] = None
    demonstration: Optional[str] = None
    verification: Optional[bool] = False
    type: Optional[str] = None

class ConceptCreate(ConceptBase):
    mathematicien_id: Optional[int]
    categorie_id: Optional[int]

class Mathematicien(BaseModel):
    id: int
    mathematicien: str

class Categorie(BaseModel):
    id: int
    category: str

class ConceptResponse(ConceptBase):
    id: int
    mathematicien: Optional[Mathematicien] = None
    categories: Optional[Categorie] = None
    sources: Optional[List["SourceResponse"]] = []
    aliases: Optional[List[str]] = []
    relations: Optional[List["RelationResponse"]] = []
    noms_etrangers: Optional[List[Dict]] = []
    date_modification: Optional[datetime]
