from pydantic import BaseModel,ConfigDict

from datetime import datetime

class TimestampModel(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes = True)
