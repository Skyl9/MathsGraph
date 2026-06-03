from typing import Optional
from datetime import date
from pydantic import BaseModel


class SearchFilters(BaseModel):
    concept: Optional[bool] = False
    mathematicien: Optional[bool] = False
    category: Optional[bool] = False
    verifiedOnly: Optional[bool] = False

    categorie_id: Optional[int] = None
    type_id: Optional[int] = None
    mathematicien_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None


class AdvancedSearchPayload(BaseModel):
    q: str
    filters: SearchFilters
