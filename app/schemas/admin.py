from pydantic import BaseModel


class Stat(BaseModel):
    users: int
    favorites: int
    concepts: int
    categories: int
    mathematicien: int


class ConceptForAdmin(BaseModel):
    id: int
    nom: str
    type: str