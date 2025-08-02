from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CommentIn(BaseModel):
    username: str | None = None
    content: str
    parent_id: int | None = None
    field:str

class CommentResponse(BaseModel):
    id: int
    concept_id: Optional[int]
    user_id: int
    content: str
    parent_id: int | None = None
    created_at: datetime
    updated_at: str
    is_deleted: bool
    field:str
    username:str


class CommentUpdate(BaseModel):
    content: str