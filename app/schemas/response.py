# app/schemas/response.py
from typing import Generic, TypeVar, Optional, Dict

from pydantic import BaseModel, Field

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    success: bool = Field(..., description="Indique si la requête a réussi", examples=[True, False])
    data: Optional[T] = Field(None, description="Les données renvoyées par la requête en cas de succès")
    error: Optional[str] = Field(
        None, description="Message d'erreur détaillé en cas d'échec", examples=["Ressource introuvable"]
    )
    meta: Optional[Dict] = Field(
        None,
        description="Métadonnées additionnelles pour la réponse (pagination, temps d'exécution...)",
        examples=[{"page": 1, "total": 42}],
    )
