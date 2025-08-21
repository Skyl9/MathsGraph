from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    tag: str


class TagsCreate(BaseModel):
    tag_name: str


class TagsUpdate(BaseModel):
    tag_id: int
    concept_id: int
