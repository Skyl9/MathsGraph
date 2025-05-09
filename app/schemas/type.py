from pydantic import BaseModel


class TypeResponse(BaseModel):
    id: int
    type: str


class TypeUpdate(BaseModel):
    field:str
    value: dict