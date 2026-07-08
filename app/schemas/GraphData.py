from typing import List, Optional, Dict

from pydantic import BaseModel, Field


class Position(BaseModel):
    x: Optional[float] = Field(None, description="Coordonnée X", examples=[10.5])
    y: Optional[float] = Field(None, description="Coordonnée Y", examples=[20.0])
    z: Optional[float] = Field(None, description="Coordonnée Z", examples=[0.0])


class Nodes(BaseModel):
    id: int = Field(..., description="Identifiant unique du nœud", examples=[1])
    nom: str = Field(..., description="Nom du nœud", examples=["Théorème de Thalès"])
    enonce: Optional[str] = Field(
        None, description="Énoncé du concept mathématique", examples=["Si deux droites parallèles..."]
    )
    typeMath: Optional[str] = Field(None, description="Type de mathématique associé", examples=["theoreme"])
    domaine: Optional[str] = Field(None, description="Domaine sémantique associé", examples=["Topologie"])
    annee: Optional[int] = Field(None, description="Année de création ou de découverte", examples=[1650])
    epoque: Optional[str] = Field(None, description="Époque de découverte", examples=["17e siècle"])
    position: Dict[str, Position] = Field(
        ..., description="Positions du nœud (ex: 2d, 3d)", examples=[{"2d": {"x": 10.5, "y": 20.0}}]
    )


class Edge(BaseModel):
    start: int = Field(..., description="ID du nœud de départ", examples=[1])
    end: int = Field(..., description="ID du nœud d'arrivée", examples=[2])
    type: str = Field(..., description="Type de relation", examples=["depend_de"])


class GraphData(BaseModel):
    nodes: Optional[List[Nodes]] = Field(None, description="Liste des nœuds constituant le graphe")
    edges: Optional[List[Edge]] = Field(None, description="Liste des arêtes reliant les nœuds")
