from typing import Optional, List

from pydantic import BaseModel, Field


class EditableField(BaseModel):
    mathematicien: List[str] = Field(
        ..., description="Liste des mathématiciens liés", examples=[["Pythagore", "Thalès"]]
    )
    categorie: List[str] = Field(..., description="Liste des catégories associées", examples=[["Géométrie", "Algèbre"]])
    type: Optional[List[str]] = Field(None, description="Types optionnels associés", examples=[["theoreme", "axiome"]])
