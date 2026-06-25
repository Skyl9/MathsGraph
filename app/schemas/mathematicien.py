from datetime import date
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from .base import TimestampModel


class MathematicienBase(BaseModel):
    nom: Optional[str] = Field(default=None, description="Le nom complet du mathématicien.", examples=["Isaac Newton"])
    biographie: Optional[str] = Field(
        default=None,
        description="Une courte biographie du mathématicien.",
        examples=["Physicien, mathématicien, astronome..."],
    )
    date_naissance: Optional[date] = Field(default=None, description="La date de naissance.", examples=["1643-01-04"])
    date_deces: Optional[date] = Field(default=None, description="La date de décès.", examples=["1727-03-31"])
    nationalite: Optional[str] = Field(
        default=None, description="La nationalité du mathématicien.", examples=["Anglais"]
    )
    domaines: Optional[List[str]] = Field(
        default=[],
        description="Les domaines d'expertise du mathématicien.",
        examples=[["Physique", "Mathématiques", "Astronomie"]],
    )
    url: Optional[str] = Field(
        default=None,
        description="URL vers une page externe (ex: Wikipédia).",
        examples=["https://fr.wikipedia.org/wiki/Isaac_Newton"],
    )
    recompense: Optional[str] = Field(
        default=None, description="Les récompenses notables obtenues.", examples=["Fellow of the Royal Society"]
    )
    epoque: Optional[str] = Field(
        default=None, description="L'époque historique à laquelle il a vécu.", examples=["XVIIe siècle"]
    )


class MathematicienResponse(MathematicienBase, TimestampModel):
    id: int = Field(description="L'identifiant unique du mathématicien.", examples=[1])


class MathematicienCreate(MathematicienBase):
    pass


class MathematicienXConcept(MathematicienBase, TimestampModel):
    id: int = Field(description="L'identifiant unique du mathématicien.", examples=[1])
    nombre_concepts: int = Field(
        default=0, description="Le nombre de concepts associés à ce mathématicien.", examples=[5]
    )


class MathematicienName(BaseModel):
    nom: str = Field(description="Le nom du mathématicien.", examples=["Isaac Newton"])
    id: int = Field(description="L'identifiant unique du mathématicien.", examples=[1])


class MathematicienUpdate(BaseModel):
    field: str = Field(description="Le champ à mettre à jour.", examples=["biographie"])
    value: Any = Field(description="La nouvelle valeur du champ.", examples=["Nouvelle biographie détaillée"])
