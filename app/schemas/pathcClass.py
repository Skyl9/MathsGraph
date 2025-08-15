from typing import List, Dict, Any, Optional

from pydantic import BaseModel


class UpdateConceptDict(BaseModel):
    field: str
    value: Any
    username:str
    note:Optional[str] = None

class CreateData(BaseModel):
    value:str

class CreateAlias(CreateData):
    id:int

class Relation(BaseModel):
    théo1:str
    théo2:str
    relation:str
    desc:str
class CreateRelation(BaseModel):
    value: Relation

class Source(BaseModel):
    id:int
    source:str
    auteur:str
    annee:int
    url:str
    type:str

class CreateSource(BaseModel):
    value:Source