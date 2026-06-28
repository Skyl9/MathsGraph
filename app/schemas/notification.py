from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


class NotificationBase(BaseModel):
    message: str = Field(..., description="Message de la notification")
    is_read: bool = Field(False, description="Indique si la notification a été lue")
    concept_id: Optional[int] = Field(None, description="ID du concept associé")


class NotificationResponse(NotificationBase):
    id: int = Field(..., description="ID de la notification")
    user_id: UUID = Field(..., description="ID de l'utilisateur")
    created_at: datetime = Field(..., description="Date de création")


class NotificationUpdate(BaseModel):
    is_read: bool = Field(..., description="Nouvel état de lecture")
