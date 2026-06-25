from pydantic import BaseModel, Field
from typing import Optional
from .base import TimestampModel


class NomEtrangerBase(BaseModel):
    nom: str = Field(description="Le nom du concept dans la langue étrangère.", examples=["Pythagorean theorem"])
    langue: str = Field(description="Le code ou le nom de la langue.", examples=["en"])
    pays: Optional[str] = Field(
        default=None, description="Le pays d'origine de cette appellation.", examples=["Royaume-Uni"]
    )
    notes: Optional[str] = Field(
        default=None,
        description="Des notes explicatives sur ce nom étranger.",
        examples=["Appellation commune dans le monde anglo-saxon"],
    )


class NomEtrangerCreate(NomEtrangerBase):
    concept_id: int = Field(description="L'identifiant du concept associé.", examples=[42])


class NomEtrangerResponse(NomEtrangerBase, TimestampModel):
    id: int = Field(description="L'identifiant unique de l'entrée.", examples=[1])
