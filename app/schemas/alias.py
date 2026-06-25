from pydantic import BaseModel, Field
from typing import Optional
from .base import TimestampModel


class AliasBase(BaseModel):
    alias: str = Field(description="Nom de l'alias", examples=["Théorème de Pythagore"])
    description: Optional[str] = Field(
        default=None,
        description="Description optionnelle de l'alias",
        examples=["Également appelé théorème de l'hypoténuse"],
    )


class AliasCreate(AliasBase):
    concept_id: int = Field(description="Identifiant du concept associé à cet alias", examples=[10])


class AliasResponse(AliasBase, TimestampModel):
    id: int = Field(description="Identifiant unique de l'alias", examples=[5])
