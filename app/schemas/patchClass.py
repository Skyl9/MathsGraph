from typing import Any, Optional

from pydantic import BaseModel, Field


class UpdateConceptDict(BaseModel):
    field: str = Field(description="Le nom du champ du concept à mettre à jour.", examples=["enonce"])
    value: Any = Field(description="La nouvelle valeur du champ.", examples=["Nouvel énoncé mis à jour"])
    username: str = Field(description="Le nom de l'utilisateur effectuant la mise à jour.", examples=["admin_user"])
    note: Optional[str] = Field(
        default=None, description="Une note explicative pour l'historique.", examples=["Correction orthographique"]
    )


class CreateData(BaseModel):
    value: str = Field(description="La valeur de la donnée à créer.", examples=["Nouvelle valeur"])


class CreateAlias(CreateData):
    id: int = Field(description="L'identifiant du concept pour lequel créer l'alias.", examples=[42])


class Relation(BaseModel):
    théo1: str = Field(
        description="Le nom ou l'identifiant du premier concept (théorème).", examples=["Théorème de Pythagore"]
    )
    théo2: str = Field(description="Le nom ou l'identifiant du deuxième concept.", examples=["Théorème de Thalès"])
    relation: str = Field(description="Le type de relation entre les deux concepts.", examples=["Généralise"])
    desc: str = Field(
        description="La description de la relation.", examples=["Le théorème 1 est un cas particulier du théorème 2"]
    )


class CreateRelation(BaseModel):
    value: Relation = Field(
        description="Les informations de la relation à créer.",
        examples=[{"théo1": "Pythagore", "théo2": "Thalès", "relation": "Généralise", "desc": "Lien détaillé"}],
    )


class Source(BaseModel):
    id: int = Field(description="L'identifiant unique de la source.", examples=[1])
    source: str = Field(description="Le nom ou le titre de la source.", examples=["Éléments d'Euclide"])
    auteur: str = Field(description="L'auteur de la source.", examples=["Euclide"])
    annee: int = Field(description="L'année de publication ou de création de la source.", examples=[-300])
    url: str = Field(
        description="L'URL permettant d'accéder à la source.",
        examples=["https://fr.wikipedia.org/wiki/Éléments_d'Euclide"],
    )
    type: str = Field(description="Le type de document de la source (livre, article, site web...).", examples=["Livre"])


class CreateSource(BaseModel):
    value: Source = Field(
        description="Les informations de la source à créer.",
        examples=[
            {"id": 1, "source": "Livre A", "auteur": "Auteur", "annee": 2000, "url": "http://...", "type": "Livre"}
        ],
    )
