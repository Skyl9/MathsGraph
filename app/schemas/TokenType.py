from pydantic import BaseModel, Field
from uuid import UUID


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Sujet du token (souvent l'username ou email)", examples=["jdupont"])
    id: UUID | str = Field(
        ..., description="Identifiant unique de l'utilisateur", examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    role: str = Field("user", description="Rôle associé au token", examples=["user", "admin"])
