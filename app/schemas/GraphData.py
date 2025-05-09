from typing import List, Optional, Dict

from pydantic import BaseModel

class Position(BaseModel):
    x:Optional[int]
    y:Optional[int]
    z:Optional[int]

class Nodes(BaseModel):
    id: int
    nom: str
    typeMath:str
    position: Dict[str, Position]


class GraphData(BaseModel):
    nodes: Optional[List[Nodes]]
    edges: Optional[List[dict]]