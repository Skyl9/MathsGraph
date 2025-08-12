# app/schemas/response.py
from typing import Generic, TypeVar, Optional, Dict

from pydantic import BaseModel
T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    success: bool
    data: Optional[T]
    error: Optional[str]
    meta:Optional[Dict]
