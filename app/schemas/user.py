from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from .base import TimestampModel


class UserBase(BaseModel):
    username: str = Field(..., description="Nom d'utilisateur unique", examples=["jdupont"])
    email: EmailStr = Field(..., description="Adresse email de l'utilisateur", examples=["jdupont@example.com"])
    is_active: bool = Field(True, description="Indique si le compte est actif", examples=[True])
    role: Optional[str] = Field(None, description="Rôle de l'utilisateur", examples=["admin"])


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, description="Mot de passe de l'utilisateur", examples=["MonMotDePasse123!"]
    )


class UserUpdate(UserBase):
    password: Optional[str] = Field(None, description="Nouveau mot de passe", examples=["NouveauMdp456!"])


class UserResponse(UserBase, TimestampModel):
    id: UUID = Field(
        ..., description="Identifiant unique de l'utilisateur", examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    preferred_language: Optional[str] = Field(None, description="Langue préférée de l'utilisateur", examples=["fr"])
    avatar_url: Optional[str] = Field(None, description="URL de l'avatar", examples=["https://example.com/avatar.jpg"])
    bio: Optional[str] = Field(None, description="Courte biographie", examples=["Passionné de maths"])


class UserInDB(UserResponse):
    hashed_password: str = Field(..., description="Mot de passe haché", examples=["$2b$12$EixZaYVK..."])


class UserId(BaseModel):
    id: UUID = Field(..., description="Identifiant de l'utilisateur", examples=["123e4567-e89b-12d3-a456-426614174000"])


class UpdateUser(BaseModel):
    field: str = Field(..., description="Champ à mettre à jour", examples=["bio"])
    value: str = Field(..., description="Nouvelle valeur du champ", examples=["Nouvelle bio"])


class Favorite(BaseModel):
    type: str = Field(..., description="Type de favori", examples=["theoreme"])
    user_id: str = Field(..., description="Identifiant de l'utilisateur", examples=["1"])
    notify_on_change: bool = Field(False, description="Activer les notifications", examples=[True])


class FavoriteResponse(BaseModel):
    id: int = Field(..., description="Identifiant du favori", examples=[42])
    nom: str = Field(..., description="Nom du favori", examples=["Théorème de Pythagore"])
    category: str = Field(..., description="Catégorie du favori", examples=["Géométrie"])
    notify_on_change: bool = Field(False, description="Notifications activées", examples=[True])
