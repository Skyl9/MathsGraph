from datetime import date
from typing import Optional, List, Any

from pydantic import BaseModel

from .base import TimestampModel


class MathematicienBase(BaseModel):
    nom: Optional[str] = None
    biographie: Optional[str] = None
    date_naissance: Optional[date] = None
    date_deces: Optional[date] = None
    nationalite: Optional[str] = None
    domaines: Optional[List[str]] = []
    url: Optional[str] = None
    recompense: Optional[str] = None
    epoque: Optional[str] = None


class MathematicienResponse(MathematicienBase, TimestampModel):
    id: int


class MathematicienCreate(MathematicienBase):
    pass


class MathematicienXConcept(MathematicienBase, TimestampModel):
    id: int
    nombre_concepts: int = 0


class MathematicienName(BaseModel):
    nom: str
    id: int


class MathematicienUpdate(BaseModel):
    field: str
    value: Any
