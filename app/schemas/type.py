from pydantic import BaseModel, Field


class TypeResponse(BaseModel):
    id: int = Field(..., description="L'identifiant unique du type", examples=[1])
    type: str = Field(..., description="La désignation ou le nom du type", examples=["Théorème", "Définition"])


class TypeNom(BaseModel):
    nom: str = Field(..., description="Le nom associé au type", examples=["Lemme"])
    id: int = Field(..., description="L'identifiant unique du type de nom", examples=[2])


class TypeUpdate(BaseModel):
    field: str = Field(..., description="Le nom du champ à mettre à jour", examples=["type"])
    value: str = Field(..., description="La nouvelle valeur pour ce champ", examples=["Nouveau Théorème"])
