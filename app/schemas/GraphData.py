from typing import List, Optional

from pydantic import BaseModel

class Position(BaseModel):
    x:int
    y:int
    z:int

class Nodes(BaseModel):
    id: int
    nom: str
    typeMath:str
    position: Position


class GraphData(BaseModel):
    nodes: Optional[List[Nodes]]
    edges: Optional[List[dict]]