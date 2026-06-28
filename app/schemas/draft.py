from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class DraftCreate(BaseModel):
    concept_id: Optional[int] = None
    draft_data: dict[str, Any]


class DraftUpdate(BaseModel):
    draft_data: dict[str, Any]


class DraftResponse(BaseModel):
    id: int
    user_id: UUID
    concept_id: Optional[int]
    draft_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
