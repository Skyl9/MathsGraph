from pydantic import BaseModel, Field
from typing import Optional
from .base import TimestampModel


class SourceBase(BaseModel):
    titre: str = Field(..., description="Le titre de la source", examples=["Éléments de mathématique"])
    auteur: Optional[str] = Field(
        None, description="L'auteur ou les auteurs de la source", examples=["Nicolas Bourbaki"]
    )
    annee: Optional[int] = Field(None, description="L'année de publication de la source", examples=[1939])
    url: Optional[str] = Field(None, description="Un lien URL vers la source", examples=["https://example.com/source"])
    type: Optional[str] = Field(
        None, description="Le type de source (livre, article, web, etc.)", examples=["livre", "article"]
    )
    details: Optional[str] = Field(
        None, description="Informations ou détails complémentaires", examples=["Tome 1 sur la théorie des ensembles"]
    )


class SourceCreate(SourceBase):
    id: int = Field(..., description="L'identifiant de la source", examples=[1])


class SourceResponse(SourceBase, TimestampModel):
    id: int = Field(..., description="L'identifiant unique de la source", examples=[10])
