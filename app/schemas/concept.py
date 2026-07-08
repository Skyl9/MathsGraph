from __future__ import annotations  # Activer les annotations différées (Python 3.7+)
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from relation import RelationResponse
    from source import SourceResponse
    from tags import Tag


class ConceptBase(BaseModel):
    nom: str = Field(description="Le nom du concept mathématique.", examples=["Théorème de Pythagore"])
    enonce: Optional[str] = Field(
        default=None,
        description="L'énoncé formel du concept.",
        examples=[
            "Dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés des deux autres côtés."
        ],
    )
    demonstration: Optional[str] = Field(
        default=None,
        description="La démonstration mathématique du concept.",
        examples=["Soit un triangle ABC rectangle en A..."],
    )
    verification: Optional[bool] = Field(
        default=False, description="Indique si le concept a été vérifié par un pair.", examples=[True]
    )
    type: Optional[str] = Field(
        default=None, description="Le type du concept (ex: théorème, lemme, conjecture).", examples=["Théorème"]
    )


class RollbackConcept(BaseModel):
    version_number: int = Field(description="Le numéro de la version à restaurer.", examples=[2])
    field_modified: str = Field(description="Le nom du champ qui a été modifié.", examples=["enonce"])
    username: str = Field(description="Le nom de l'utilisateur ayant demandé le rollback.", examples=["admin"])


class ConceptCreate(ConceptBase):
    mathematicien_id: Optional[int] = Field(
        default=None, description="L'identifiant du mathématicien associé au concept.", examples=[1]
    )
    categorie_id: Optional[int] = Field(
        default=None, description="L'identifiant de la catégorie du concept.", examples=[5]
    )


class Mathematicien(BaseModel):
    id: int = Field(description="L'identifiant unique du mathématicien.", examples=[1])
    mathematicien: str = Field(description="Le nom complet du mathématicien.", examples=["Pythagore de Samos"])


class Categorie(BaseModel):
    id: int = Field(description="L'identifiant unique de la catégorie.", examples=[5])
    category: str = Field(description="Le nom de la catégorie.", examples=["Géométrie"])


class ConceptName(BaseModel):
    nom: str = Field(description="Le nom du concept.", examples=["Théorème de Pythagore"])
    id: int = Field(description="L'identifiant unique du concept.", examples=[42])


class ConceptResponse(ConceptBase):
    id: int = Field(description="L'identifiant unique du concept.", examples=[42])
    mathematicien: Optional[Mathematicien] = Field(
        default=None, description="Les informations du mathématicien associé."
    )
    categorie: Optional[Categorie] = Field(default=None, description="La catégorie du concept.")
    sources: Optional[List["SourceResponse"]] = Field(default=[], description="Les sources associées au concept.")
    aliases: Optional[List[str]] = Field(
        default=[], description="Les alias ou autres noms du concept.", examples=[["Théorème de la corde"]]
    )
    relations: Optional[List["RelationResponse"]] = Field(
        default=[], description="Les relations avec d'autres concepts."
    )
    noms_etrangers: Optional[List[Dict]] = Field(
        default=[], description="Les traductions ou noms étrangers du concept."
    )
    date_modification: Optional[datetime] = Field(
        default=None, description="La date de la dernière modification.", examples=["2026-06-25T14:30:00Z"]
    )
    tags: Optional[List["Tag"]] = Field(default=[], description="Les tags associés au concept.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 42,
                    "nom": "Théorème de Pythagore",
                    "enonce": "Dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés des deux autres côtés.",
                    "demonstration": "Soit un triangle ABC rectangle en A...",
                    "verification": True,
                    "type": "Théorème",
                    "mathematicien": {"id": 1, "mathematicien": "Pythagore de Samos"},
                    "categorie": {"id": 5, "category": "Géométrie"},
                    "sources": [{"id": 1, "source": "Livre I des Éléments d'Euclide"}],
                    "aliases": ["Théorème de la corde"],
                    "relations": [
                        {
                            "id": 10,
                            "type_relation": "implication",
                            "concept_cible": {"id": 8, "nom": "Axiome d'Euclide"},
                        }
                    ],
                    "noms_etrangers": [{"nom": "Pythagorean theorem", "langue": "en", "pays": "UK"}],
                    "date_modification": "2026-06-25T14:30:00Z",
                    "tags": [{"id": 1, "tag": "Géométrie"}],
                }
            ]
        }
    }


class WantedConcept(BaseModel):
    id: int = Field(description="L'identifiant unique du concept.")
    nom: str = Field(description="Le nom du concept.")
    categorie: Optional[str] = Field(default=None, description="La catégorie du concept.")
    missing_fields: List[str] = Field(description="Liste des champs manquants (ex: demonstration, sources).")
