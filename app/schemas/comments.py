from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentIn(BaseModel):
    username: str | None = Field(
        default=None, description="Nom d'utilisateur facultatif (si anonyme ou récupéré du token)", examples=["johndoe"]
    )
    content: str = Field(description="Contenu du commentaire", examples=["Très bonne explication du théorème."])
    parent_id: int | None = Field(
        default=None, description="Identifiant du commentaire parent en cas de réponse", examples=[5]
    )
    field: str = Field(description="Champ ou section associée au commentaire", examples=["demonstration"])


class CommentResponse(BaseModel):
    id: int = Field(description="Identifiant unique du commentaire", examples=[1])
    concept_id: Optional[int] = Field(default=None, description="Identifiant du concept lié", examples=[10])
    user_id: int = Field(description="Identifiant de l'utilisateur ayant posté", examples=[2])
    content: str = Field(description="Contenu du commentaire", examples=["Très bonne explication du théorème."])
    parent_id: int | None = Field(default=None, description="Identifiant du commentaire parent", examples=[5])
    created_at: datetime = Field(description="Date de création", examples=["2023-10-25T14:30:00Z"])
    updated_at: datetime = Field(description="Date de dernière mise à jour", examples=["2023-10-26T09:15:00Z"])
    is_deleted: bool = Field(description="Indique si le commentaire a été supprimé (soft delete)", examples=[False])
    field: str = Field(description="Champ associé", examples=["demonstration"])
    username: str = Field(description="Nom d'utilisateur de l'auteur", examples=["johndoe"])


class CommentUpdate(BaseModel):
    content: str = Field(description="Nouveau contenu du commentaire", examples=["Explication corrigée et améliorée."])
