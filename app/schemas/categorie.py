from pydantic import BaseModel, Field
from typing import Optional, Any


class CategorieBase(BaseModel):
    id: int = Field(description="Identifiant unique de la catégorie", examples=[1])
    nom: str = Field(description="Nom de la catégorie", examples=["Algèbre"])
    description: Optional[str] = Field(
        default=None, description="Description de la catégorie", examples=["Branche des mathématiques"]
    )
    parent_id: Optional[int] = Field(default=None, description="Identifiant de la catégorie parente", examples=[2])


class CategoryUpdate(BaseModel):
    field: str = Field(description="Nom du champ à mettre à jour", examples=["nom"])
    value: Any = Field(description="Nouvelle valeur pour le champ", examples=["Nouvelle Algèbre"])
