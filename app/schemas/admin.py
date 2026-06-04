from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Stat(BaseModel):
    users: int
    favorites: int
    concepts: int
    categories: int
    mathematicien: int
    users_growth: Optional[int] = 0
    concepts_growth: Optional[int] = 0


class ConceptForAdmin(BaseModel):
    id: int
    nom: str
    type: str


class ApiRouteMetric(BaseModel):
    method: str
    endpoint: str
    total_hits: int
    avg_duration: float


class DailyHit(BaseModel):
    date: str
    hits: int


class ApiAnalytics(BaseModel):
    daily_hits: int
    top_routes: List[ApiRouteMetric]
    weekly_hits: List[DailyHit]


class RecentActivityItem(BaseModel):
    id: int
    nom: str
    type: str  # 'concept', 'category', 'user'
    action: str  # 'creation', 'update'
    date: datetime
