from pydantic import BaseModel


class Views(BaseModel):
    total_views: int
    unique_views: int