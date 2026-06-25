from pydantic import BaseModel, ConfigDict, Field

from datetime import datetime


class TimestampModel(BaseModel):
    created_at: datetime | None = Field(
        default=None, description="Date et heure de création", examples=["2023-10-25T14:30:00Z"]
    )
    updated_at: datetime | None = Field(
        default=None, description="Date et heure de dernière mise à jour", examples=["2023-10-26T09:15:00Z"]
    )
    model_config = ConfigDict(from_attributes=True)
