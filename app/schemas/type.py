from pydantic import BaseModel


class TypeResponse(BaseModel):
    id: int
    type: str

class TypeNom(BaseModel):
    nom: str
    id: int

class TypeUpdate(BaseModel):
    field:str
    value: str