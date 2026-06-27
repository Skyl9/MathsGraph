from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    concept: Optional[bool] = Field(False, description="Inclure les concepts dans la recherche", examples=[True])
    mathematicien: Optional[bool] = Field(
        False, description="Inclure les mathématiciens dans la recherche", examples=[True]
    )
    category: Optional[bool] = Field(False, description="Inclure les catégories dans la recherche", examples=[False])
    verifiedOnly: Optional[bool] = Field(
        False, description="Limiter la recherche aux éléments vérifiés", examples=[True]
    )

    categorie_id: Optional[int] = Field(
        None, description="Filtrer par un identifiant de catégorie spécifique", examples=[1]
    )
    type_id: Optional[int] = Field(None, description="Filtrer par un type spécifique", examples=[2])
    mathematicien_id: Optional[int] = Field(
        None, description="Filtrer par un identifiant de mathématicien spécifique", examples=[42]
    )
    date_start: Optional[date] = Field(
        None, description="Date de début pour le filtre chronologique", examples=["1900-01-01"]
    )
    date_end: Optional[date] = Field(
        None, description="Date de fin pour le filtre chronologique", examples=["2000-12-31"]
    )


class AdvancedSearchPayload(BaseModel):
    q: str = Field(..., description="La requête de recherche principale (texte libre)", examples=["Géométrie"])
    filters: SearchFilters = Field(..., description="Filtres avancés à appliquer à la recherche")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "q": "Géométrie non euclidienne",
                    "filters": {
                        "concept": True,
                        "mathematicien": False,
                        "category": False,
                        "verifiedOnly": True,
                        "categorie_id": 5,
                        "type_id": 2,
                        "mathematicien_id": None,
                        "date_start": "1800-01-01",
                        "date_end": "1900-12-31",
                    },
                }
            ]
        }
    }
