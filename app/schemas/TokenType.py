from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Sujet du token (souvent l'username ou email)", examples=["jdupont"])
    id: int | str = Field(..., description="Identifiant unique de l'utilisateur", examples=[1])
    role: str = Field("user", description="Rôle associé au token", examples=["user", "admin"])
