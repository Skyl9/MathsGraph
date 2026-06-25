from pydantic import BaseModel, Field


class Views(BaseModel):
    total_views: int = Field(..., description="Nombre total de vues", examples=[1500])
    unique_views: int = Field(..., description="Nombre de vues uniques", examples=[1200])
