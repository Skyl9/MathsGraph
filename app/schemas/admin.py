from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Stat(BaseModel):
    users: int = Field(description="Nombre total d'utilisateurs inscrits", examples=[150])
    favorites: int = Field(description="Nombre total de favoris enregistrés", examples=[42])
    concepts: int = Field(description="Nombre total de concepts mathématiques", examples=[300])
    categories: int = Field(description="Nombre total de catégories", examples=[15])
    mathematicien: int = Field(description="Nombre total de mathématiciens", examples=[50])
    users_growth: Optional[int] = Field(
        default=0, description="Croissance des utilisateurs sur la dernière période", examples=[5]
    )
    concepts_growth: Optional[int] = Field(
        default=0, description="Croissance des concepts sur la dernière période", examples=[12]
    )


class ConceptForAdmin(BaseModel):
    id: int = Field(description="Identifiant unique du concept", examples=[1])
    nom: str = Field(description="Nom du concept", examples=["Théorème de Pythagore"])
    type: str = Field(description="Type de l'entité", examples=["concept"])


class ApiRouteMetric(BaseModel):
    method: str = Field(description="Méthode HTTP", examples=["GET"])
    endpoint: str = Field(description="Chemin de la route", examples=["/api/v1/concepts"])
    total_hits: int = Field(description="Nombre total d'appels à cette route", examples=[1540])
    avg_duration: float = Field(description="Durée moyenne d'exécution en millisecondes", examples=[45.2])


class DailyHit(BaseModel):
    date: str = Field(description="Date au format ISO", examples=["2023-10-25"])
    hits: int = Field(description="Nombre d'appels ce jour-là", examples=[350])


class ApiAnalytics(BaseModel):
    daily_hits: int = Field(description="Total des appels sur la journée", examples=[1200])
    top_routes: List[ApiRouteMetric] = Field(description="Liste des routes les plus appelées")
    weekly_hits: List[DailyHit] = Field(description="Historique des appels sur la semaine")


class RecentActivityItem(BaseModel):
    id: int = Field(description="Identifiant de l'élément modifié", examples=[1])
    nom: str = Field(description="Nom de l'élément", examples=["Théorème de Thalès"])
    type: str = Field(description="Type de l'entité", examples=["concept"])  # 'concept', 'category', 'user'
    action: str = Field(description="Type d'action effectuée", examples=["creation"])  # 'creation', 'update'
    date: datetime = Field(description="Date et heure de l'action", examples=["2023-10-25T14:30:00Z"])
