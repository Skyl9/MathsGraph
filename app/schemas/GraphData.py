from typing import List, Optional, Dict

from pydantic import BaseModel

class Position(BaseModel):
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]

class Nodes(BaseModel):
    id: int
    nom: str
    enonce: Optional[str] = None
    typeMath: Optional[str] = None
    position: Dict[str, Position]

class Edge(BaseModel):
    start: int
    end: int
    type: str

class GraphData(BaseModel):
    nodes: Optional[List[Nodes]]
    edges: Optional[List[Edge]]