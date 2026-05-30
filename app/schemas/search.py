from pydantic import BaseModel

class AdvancedSearchPayload(BaseModel):
    q: str
    filters: dict
