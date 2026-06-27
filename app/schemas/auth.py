from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, Field


class Token(BaseModel):
    access_token: str = Field(description="Jeton d'accès JWT", examples=["eyJhbGci..."])
    token_type: str = Field(description="Type de jeton", examples=["bearer"])


class UserCreate(BaseModel):
    username: str = Field(description="Nom d'utilisateur", examples=["johndoe"])
    email: EmailStr = Field(description="Adresse email de l'utilisateur", examples=["john.doe@example.com"])
    password: str = Field(description="Mot de passe en clair (sera hashé)", examples=["MonMotDePasseSecret123!"])

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        return v

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom d'utilisateur ne peut pas être vide.")
        if len(v) < 2:
            raise ValueError("Le nom d'utilisateur doit contenir au moins 2 caractères.")
        return v


class User(BaseModel):
    id: UUID = Field(
        description="Identifiant unique de l'utilisateur", examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    username: str = Field(description="Nom d'utilisateur", examples=["johndoe"])
    email: str = Field(description="Adresse email", examples=["john.doe@example.com"])
    is_active: bool = Field(description="Indique si le compte est actif", examples=[True])
    role: Optional[str] = Field(default=None, description="Rôle de l'utilisateur", examples=["admin"])
    created_at: Optional[datetime] = Field(
        default=None, description="Date de création du compte", examples=["2023-10-25T14:30:00Z"]
    )


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr = Field(description="Adresse email pour la réinitialisation", examples=["john.doe@example.com"])


class PasswordResetConfirmSchema(BaseModel):
    new_password: str = Field(description="Nouveau mot de passe", examples=["NouveauMotDePasse123!"])
    token: str = Field(description="Jeton de réinitialisation", examples=["abc123token"])

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        return v
