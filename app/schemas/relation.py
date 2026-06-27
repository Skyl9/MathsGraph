from typing import Optional, Literal

from pydantic import BaseModel, Field


class RelationType(BaseModel):
    id: int = Field(..., description="L'identifiant unique de la relation", examples=[1, 2])
    description: Optional[str] = Field(
        None, description="Description détaillée de la relation", examples=["Cette relation implique que..."]
    )
    date_relation: Optional[str] = Field(
        None, description="Date ou époque de la relation", examples=["19ème siècle", "2024-01-01"]
    )


class RelationCreate(RelationType):
    pass


class ConceptRelation(BaseModel):
    id: int = Field(..., description="L'identifiant du concept impliqué dans la relation", examples=[42])
    nom: str = Field(..., description="Le nom du concept", examples=["Théorème de Pythagore"])


class RelationResponse(RelationType):
    concept_source: ConceptRelation = Field(..., description="Le concept source de la relation")
    concept_cible: ConceptRelation = Field(..., description="Le concept cible de la relation")
    type_relation: Literal["reciproque", "equivalence", "implication", "utilise"] = Field(
        ..., description="Le type de la relation", examples=["implication"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "description": "Corollaire direct",
                    "date_relation": "19ème siècle",
                    "concept_source": {"id": 10, "nom": "Théorème de Pythagore"},
                    "concept_cible": {"id": 12, "nom": "Distance euclidienne"},
                    "type_relation": "implication",
                }
            ]
        }
    }
